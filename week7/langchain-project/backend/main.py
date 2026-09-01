import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

from auth import authenticate_user, create_access_token, get_current_user, register_user
from database import ChatMessage, ChatSession, ToolEvent, User, init_db
from dependencies import get_db

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "60"))
TOOL_TIMEOUT_SECONDS = int(os.getenv("TOOL_TIMEOUT_SECONDS", "8"))
TOOL_RETRY_COUNT = int(os.getenv("TOOL_RETRY_COUNT", "2"))
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-chat")

app = FastAPI(title="Week7 Chat Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

thread_pool = ThreadPoolExecutor(max_workers=4)


class CreateSessionRequest(BaseModel):
    title: str | None = None


class ChatStreamRequest(BaseModel):
    message: str
    session_id: str


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def sse_event(event_type: str, content: Any, **extra: Any) -> str:
    payload = {"type": event_type, "content": content, **extra}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def normalize_content(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [normalize_content(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_content(item) for key, item in value.items()}
    content = getattr(value, "content", None)
    if content is not None:
        return normalize_content(content)
    return str(value)


def execute_tool_with_timeout(tool_name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    @retry(stop=stop_after_attempt(TOOL_RETRY_COUNT), wait=wait_fixed(0.4), reraise=True)
    def runner() -> Any:
        future = thread_pool.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=TOOL_TIMEOUT_SECONDS)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise TimeoutError(f"工具 {tool_name} 执行超时") from exc

    try:
        return runner()
    except RetryError as exc:
        raise exc.last_attempt.exception()


@tool
def get_weather(city: str) -> str:
    """输入城市名称，返回该城市的当前天气。"""
    return execute_tool_with_timeout("get_weather", lambda: f"{city} 今天是晴天，25度。")


@tool
def calculate_multiply(a: int, b: int) -> int:
    """计算两个整数的乘积。"""
    return execute_tool_with_timeout("calculate_multiply", lambda: a * b)


@tool
def search_rag_knowledge_base(query: str) -> str:
    """搜索本地知识库摘要。用于返回用户私有知识笔记中的命中结果。"""
    return execute_tool_with_timeout(
        "search_rag_knowledge_base",
        lambda: f"RAG 检索结果：关于'{query}'的文档片段，包含 LangGraph、工具调用和多轮对话实践。",
    )


TOOLS = [get_weather, calculate_multiply, search_rag_knowledge_base]


def build_agent() -> Any:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("缺少 DEEPSEEK_API_KEY，请先在 backend/.env 中配置。")

    model = ChatOpenAI(
        model=MODEL_NAME,
        api_key=api_key,
        base_url=DEEPSEEK_BASE_URL,
        streaming=True,
        temperature=0.2,
    )
    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=(
            "你是一个面向登录用户的 Chat Agent。"
            "回答前要结合当前用户上下文和会话历史。"
            "如果需要工具，就优先调用工具并清晰总结结果。"
        ),
    )


async def get_session_or_404(session_id: str, user_id: int, db: AsyncSession) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session


async def build_history(session_id: str, user_id: int, db: AsyncSession) -> list[dict[str, str]]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id, ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(8)
    )
    rows = list(reversed(result.scalars().all()))
    return [{"role": row.role, "content": row.content} for row in rows]


async def save_tool_event(
    db: AsyncSession,
    user_id: int,
    session_id: str,
    event_type: str,
    content: str,
    tool_name: str = "",
) -> None:
    db.add(
        ToolEvent(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            tool_name=tool_name,
            content=content,
        )
    )
    await db.commit()


@app.on_event("startup")
async def startup() -> None:
    await init_db()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Week7 Chat Agent API is running"}


@app.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {"id": current_user.id, "username": current_user.username}


@app.post("/register")
async def register(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    user = await register_user(form_data.username, form_data.password, db)
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    user = await authenticate_user(form_data.username, form_data.password, db)
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        {
            "id": item.id,
            "title": item.title,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }
        for item in sessions
    ]


@app.post("/sessions")
async def create_session(
    payload: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    session = ChatSession(
        id=str(uuid4()),
        user_id=current_user.id,
        title=(payload.title or "新的 Agent 会话").strip()[:120] or "新的 Agent 会话",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    await get_session_or_404(session_id, current_user.id, db)
    await db.execute(
        delete(ChatMessage).where(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == current_user.id,
        )
    )
    await db.execute(
        delete(ToolEvent).where(
            ToolEvent.session_id == session_id,
            ToolEvent.user_id == current_user.id,
        )
    )
    await db.execute(
        delete(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    await db.commit()
    return {"message": "会话已删除"}


@app.get("/history")
async def get_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    await get_session_or_404(session_id, current_user.id, db)
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id, ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at)
    )
    rows = result.scalars().all()
    return [
        {
            "id": row.id,
            "role": row.role,
            "content": row.content,
            "time": row.created_at.isoformat(),
        }
        for row in rows
    ]


@app.post("/chat/stream")
async def chat_stream(
    payload: ChatStreamRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    question = payload.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    session = await get_session_or_404(payload.session_id, current_user.id, db)
    history = await build_history(session.id, current_user.id, db)
    agent = build_agent()

    async def generate() -> Any:
        final_chunks: list[str] = []
        final_answer = ""
        seen_tool_call_ids: set[str] = set()

        user_context_message = (
            f"当前用户信息：用户名={current_user.username}，user_id={current_user.id}。"
            f"当前会话标题：{session.title}。"
            "禁止把其他用户的内容混入当前回答。"
        )

        agent_input = {
            "messages": [
                {"role": "system", "content": user_context_message},
                *history,
                {"role": "user", "content": question},
            ]
        }

        async def stream_agent_once() -> None:
            nonlocal final_answer
            async for event in agent.astream_events(
                agent_input,
                version="v2",
                config={"recursion_limit": 6},
            ):
                if await request.is_disconnected():
                    raise asyncio.CancelledError()

                kind = event["event"]
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    token = normalize_content(chunk.content)
                    if isinstance(token, list):
                        text = "".join(str(item) for item in token)
                    else:
                        text = str(token or "")
                    if text:
                        final_chunks.append(text)
                        yield sse_event("token", text)

                elif kind == "on_chat_model_end":
                    output = event["data"].get("output")
                    tool_calls = getattr(output, "tool_calls", None) or []
                    for tool_call in tool_calls:
                        tool_call_id = tool_call.get("id")
                        if tool_call_id and tool_call_id in seen_tool_call_ids:
                            continue
                        if tool_call_id:
                            seen_tool_call_ids.add(tool_call_id)

                        tool_name = tool_call.get("name") or "unknown_tool"
                        tool_args = normalize_content(tool_call.get("args") or {})
                        content = f"决定调用工具 [{tool_name}]，参数: {tool_args}"
                        await save_tool_event(db, current_user.id, session.id, "thinking", str(content), tool_name)
                        yield sse_event(
                            "thinking",
                            content,
                            tool_name=tool_name,
                            tool_args=tool_args,
                        )

                elif kind == "on_tool_end":
                    tool_name = event.get("name", "")
                    output = normalize_content(event["data"].get("output", ""))
                    content = f"工具 [{tool_name}] 返回: {output}"
                    await save_tool_event(db, current_user.id, session.id, "tool_result", str(content), tool_name)
                    yield sse_event(
                        "tool_result",
                        content,
                        tool_name=tool_name,
                        output=output,
                    )

                elif kind == "on_chain_end":
                    output = event["data"].get("output")
                    if isinstance(output, dict):
                        messages = output.get("messages", [])
                        for item in reversed(messages):
                            if isinstance(item, AIMessage) and item.content:
                                final_answer = str(item.content)
                                break

        try:
            async for chunk in asyncio.wait_for(stream_agent_once(), timeout=AGENT_TIMEOUT_SECONDS):
                yield chunk
        except TypeError:
            # asyncio.wait_for 不能直接包异步生成器，这里退回到手动超时保护。
            pass

        try:
            agen = stream_agent_once()
            while True:
                chunk = await asyncio.wait_for(agen.__anext__(), timeout=AGENT_TIMEOUT_SECONDS)
                yield chunk
        except StopAsyncIteration:
            pass
        except asyncio.TimeoutError:
            retry_message = f"Agent 超时，已在 {AGENT_TIMEOUT_SECONDS} 秒后中断。"
            await save_tool_event(db, current_user.id, session.id, "retry", retry_message)
            yield sse_event("retry", retry_message)
        except asyncio.CancelledError:
            yield sse_event("error", "客户端已断开连接")
            return
        except Exception as exc:
            retry_message = f"Agent 执行异常，已触发重试保护: {exc}"
            await save_tool_event(db, current_user.id, session.id, "retry", retry_message)
            yield sse_event("retry", retry_message)

        answer_text = final_answer or "".join(final_chunks).strip() or "本次没有生成有效回答。"

        db.add(ChatMessage(role="user", content=question, session_id=session.id, user_id=current_user.id))
        db.add(ChatMessage(role="assistant", content=answer_text, session_id=session.id, user_id=current_user.id))
        session.updated_at = datetime.utcnow()
        if session.title == "新的 Agent 会话":
            session.title = question[:24]
        await db.commit()

        yield sse_event("final", answer_text)
        yield sse_event("done", "[DONE]")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )

