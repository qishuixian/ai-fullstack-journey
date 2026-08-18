import json
import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiofiles
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import authenticate_user, create_access_token, get_current_user, register_user
from database import ChatMessage, User, UserFile, init_db
from dependencies import get_db


load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"

app = FastAPI(title="RAG Knowledge Base")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
VECTOR_DIR = BASE_DIR / "chroma_db"

ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=300,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""],
)
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
vectordb = Chroma(embedding_function=embeddings, persist_directory=str(VECTOR_DIR))
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com/v1",
    temperature=0,
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, Any]] = []
    session_id: str = "default"


class UpdateMessageRequest(BaseModel):
    content: str


@app.on_event("startup")
async def startup():
    await init_db()


@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start_time)
    return response


def build_user_filter(user_id: int) -> dict[str, Any]:
    # 默认检索范围就是“当前用户的所有文件”，避免串到其他用户数据。
    return {"user_id": str(user_id)}


def build_file_filter(user_id: int, file_id: str) -> dict[str, Any]:
    # 删除向量时同时带上 user_id，避免误删到同一集合中的其他用户文档。
    return {"$and": [{"user_id": str(user_id)}, {"file_id": file_id}]}


async def index_pdf_file(file_record: UserFile) -> int:
    loader = PyPDFLoader(file_record.file_path)
    docs = loader.load()
    splits = text_splitter.split_documents(docs)
    for index, doc in enumerate(splits):
        # 把用户和文件归属写进 metadata，后续检索/删除都依赖这些字段过滤。
        doc.metadata.update(
            {
                "user_id": str(file_record.user_id),
                "file_id": file_record.id,
                "filename": file_record.original_filename,
                "chunk_index": index,
            }
        )
    vectordb.add_documents(splits)
    return len(splits)


@app.post("/register")
async def register(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await register_user(form_data.username, form_data.password, db)
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(form_data.username, form_data.password, db)
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/files")
async def get_files(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(UserFile)
        .where(UserFile.user_id == current_user.id)
        .order_by(UserFile.created_at.desc())
    )
    result = await db.execute(stmt)
    files = result.scalars().all()
    return [
        {
            "id": item.id,
            "filename": item.original_filename,
            "size": item.size,
            "created_at": item.created_at.isoformat(),
        }
        for item in files
    ]


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持上传 PDF 文件")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

    file_id = str(uuid4())
    stored_filename = f"{file_id}{ext}"
    file_path = UPLOAD_DIR / stored_filename

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    record = UserFile(
        id=file_id,
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        size=len(content),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    try:
        chunks = await index_pdf_file(record)
    except Exception as exc:
        # 如果切分或入库失败，要把元数据记录和落盘文件一起回滚掉。
        await db.execute(delete(UserFile).where(UserFile.id == record.id))
        await db.commit()
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"处理 PDF 失败: {exc}")

    return {
        "id": record.id,
        "filename": record.original_filename,
        "size": record.size,
        "chunks": chunks,
    }


@app.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(UserFile).where(UserFile.id == file_id, UserFile.user_id == current_user.id)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 先删 ChromaDB 中对应向量，再删业务表记录，保证后续提问不再命中该文件。
    vectordb._collection.delete(where=build_file_filter(current_user.id, file_id))
    await db.execute(delete(UserFile).where(UserFile.id == file_id))
    await db.commit()

    file_path = Path(file_record.file_path)
    if file_path.exists():
        file_path.unlink()

    return {"message": "文件已删除"}


@app.get("/history")
async def get_history(
    session_id: str = "default",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id, ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()
    return [
        {
            "id": item.id,
            "role": item.role,
            "content": item.content,
            "time": item.created_at.isoformat(),
        }
        for item in messages
    ]


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = request.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    candidate_docs = vectordb.similarity_search(
        question,
        k=10,
        filter=build_user_filter(current_user.id),
    )

    context_str = "\n\n".join(
        f"[文件: {doc.metadata.get('filename', '未知文件')}]\n{doc.page_content}"
        for doc in candidate_docs
    )
    if not context_str:
        context_str = "当前用户还没有上传任何可检索的 PDF 文件。"

    messages = [
        SystemMessage(
            content=(
                "你是一个知识库问答助手。优先基于给定上下文回答问题。"
                "如果上下文不足，请明确说明，并只做谨慎推断。"
            )
        ),
        HumanMessage(content=f"上下文：\n{context_str}\n\n问题：\n{question}\n\n请回答："),
    ]

    stream = llm.stream(messages)

    async def generate():
        full_reply = ""
        for chunk in stream:
            content = getattr(chunk, "content", "")
            if not content:
                continue
            full_reply += content
            # 用 SSE 增量推给前端，保持和现有流式聊天 UI 对齐。
            yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

        # 只在完整回答结束后落库，避免中途消息残缺。
        db.add(
            ChatMessage(
                role="user",
                content=question,
                session_id=request.session_id,
                user_id=current_user.id,
            )
        )
        db.add(
            ChatMessage(
                role="assistant",
                content=full_reply or "未检索到可回答的内容。",
                session_id=request.session_id,
                user_id=current_user.id,
            )
        )
        await db.commit()
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.patch("/messages/{message_id}")
async def update_message(
    message_id: int,
    request: UpdateMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ChatMessage).where(ChatMessage.id == message_id, ChatMessage.user_id == current_user.id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")

    message.content = request.content
    await db.commit()
    return {"message": "消息已更新"}


@app.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ChatMessage).where(ChatMessage.id == message_id, ChatMessage.user_id == current_user.id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")

    await db.execute(delete(ChatMessage).where(ChatMessage.id == message_id))
    await db.commit()
    return {"message": "消息已删除"}


@app.get("/")
async def root():
    return {"message": "RAG API is running"}
