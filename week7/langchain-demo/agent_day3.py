import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- 1. 初始化 FastAPI ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境请限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. 定义工具和模型 (复用 Day 2) ---
@tool
def get_weather(location: str) -> str:
    """输入城市名称，返回该城市的当前天气。"""
    return f"{location} 今天是晴天，25度。"

@tool
def calculate_multiply(a: int, b: int) -> int:
    """计算两个整数的乘积。"""
    return a * b

@tool
def search_rag_knowledge_base(query: str) -> str:
    """搜索本地 RAG 知识库。用于查询历史文档、个人笔记或专有知识。"""
    print(f"[调试] 执行了 RAG 搜索工具，查询: {query}")
    return f"RAG 检索结果：关于'{query}'的文档片段..."


tools = [get_weather, calculate_multiply, search_rag_knowledge_base]


def build_agent():
    """创建兼容 LangChain 1.x 的工具调用 Agent。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "缺少 DEEPSEEK_API_KEY。请在当前终端先执行 "
            "`$env:DEEPSEEK_API_KEY=\"你的key\"`，或在项目目录创建 .env 文件并写入 "
            "`DEEPSEEK_API_KEY=你的key`。"
        )

    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        streaming=True,
    )
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt="你是一个全栈开发专家助手。你可以使用工具来回答问题。如果不需要工具，请直接回答。",
    )


def normalize_content(value):
    """把 LangChain 事件中的复杂对象转成可序列化文本。"""
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


def sse_event(event_type: str, content, **extra) -> str:
    payload = {"type": event_type, "content": normalize_content(content)}
    if extra:
        payload.update({key: normalize_content(value) for key, value in extra.items()})
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

# --- 3. SSE 流式生成器 ---
async def generate_stream(user_query: str):
    """
    核心逻辑：异步生成器，持续产出 SSE 格式的数据
    SSE 格式要求：data: {json}\n\n (双换行结尾)
    """
    try:
        agent = build_agent()
        final_chunks = []
        seen_tool_call_ids = set()

        async for event in agent.astream_events(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_query,
                    }
                ]
            },
            version="v2",
            config={"recursion_limit": 5},
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                tool_calls = getattr(chunk, "tool_call_chunks", None) or []
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name") or "unknown_tool"
                    tool_args = tool_call.get("args") or ""
                    if tool_name or tool_args:
                        yield sse_event(
                            "thinking",
                            f"决定调用工具 [{tool_name}]，参数片段: {tool_args}",
                            tool_name=tool_name,
                            tool_args=tool_args,
                        )
                        await asyncio.sleep(0.05)
                token = chunk.content
                if token:
                    if isinstance(token, list):
                        text = "".join(
                            item.get("text", "") for item in token if isinstance(item, dict)
                        )
                    else:
                        text = str(token)
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
                    tool_args = tool_call.get("args") or {}
                    yield sse_event(
                        "thinking",
                        f"决定调用工具 [{tool_name}]，参数: {tool_args}",
                        tool_name=tool_name,
                        tool_args=tool_args,
                    )
                    await asyncio.sleep(0.05)

            # 2. 捕获工具执行后的返回结果
            elif kind == "on_tool_end":
                tool_name = event.get("name", "")
                output = event["data"].get("output", "")
                yield sse_event(
                    "tool_result",
                    f"工具 [{tool_name}] 返回: {output}",
                    tool_name=tool_name,
                    output=output,
                )

            elif kind == "on_chain_end":
                output = event["data"].get("output")
                if isinstance(output, dict):
                    messages = output.get("messages", [])
                    for message in reversed(messages):
                        if isinstance(message, AIMessage) and message.content:
                            final_answer = str(message.content)
                            if final_answer and "".join(final_chunks).strip() != final_answer.strip():
                                yield sse_event("final", final_answer)
                            break

        # 4. 发送结束信号
        yield sse_event("done", "[DONE]")

    except Exception as e:
        # 流式中途报错处理：通过 SSE 推送错误信息
        yield sse_event("error", str(e))

# --- 4. 暴露 SSE 接口 ---
@app.post("/api/chat/stream")
async def chat_stream(request: Request):
    """接收前端提问，返回 SSE 流式响应"""
    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        return StreamingResponse(
            iter([sse_event("error", "question 不能为空"), sse_event("done", "[DONE]")]),
            media_type="text/event-stream",
        )
    
    # 返回 StreamingResponse，设置 media_type 为 text/event-stream
    return StreamingResponse(
        generate_stream(question), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",       # 禁止缓存
            "X-Accel-Buffering": "no",         # 告诉 Nginx 不要缓冲（生产环境必加）
            "Connection": "keep-alive"
        }
    )

# 本地测试运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
