# -*- coding: utf-8 -*-
import os
import json
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import delete, select
from database import User, async_session, ChatMessage, init_db, Session
from uuid import uuid4
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from auth import (
    SECRET_KEY, ALGORITHM, register_user, authenticate_user, create_access_token, get_current_user
)
from fastapi.security import OAuth2PasswordRequestForm


load_dotenv()

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

class ChatRequest(BaseModel):
    message: str
    history: list = []  # 历史记录，可选
    session_id: str = "default"  # 会话ID
# 中间件所有HTTP请求都要经过
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 计算耗时
    process_time = time.time() - start_time
    
    # 添加自定义响应头（方便调试）
    response.headers["X-Process-Time"] = str(process_time)
    
    # 打印日志（生产环境建议用 logging 模块）
    print(f"[{request.method}] {request.url.path} - {process_time:.3f}s")
    
    return response

# @app.middleware("http")
# async def restrict_access_time(request: Request, call_next):
#     hour = time.localtime().tm_hour
#     if hour < 8 or hour > 23:
#         return JSONResponse(
#             status_code=403,
#             content={"message": "牛马夜间休息，请白天再来"}
#         )
#     response = await call_next(request)
#     return response
# ---- 原有的非流式接口（保留用于对比） ----
@app.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        messages = [{"role": "system", "content": "你是一个友善的AI助手。"}]
        for msg in request.history:
            messages.append(msg)
        messages.append({"role": "user", "content": request.message})

        response = client.chat.completions.create(
            model="deepseek-chat",  # 如果报错请改为 deepseek-v4-flash
            messages=messages,
            stream=False
        )
        reply = response.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- 新增的流式接口 ----
@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        messages = [{"role": "system", "content": "你是一个友善的AI助手。"}]
        for msg in request.history:
            messages.append(msg)
        messages.append({"role": "user", "content": request.message})

        # 调用 DeepSeek 流式 API
        stream = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            stream=True
        )

        # 定义一个生成器，逐块产生 SSE 格式的数据
        async def generate():
            full_reply = ""  # 用于累积完整回复
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_reply += content
                    # SSE 格式：data: <json>\n\n
                    yield f"data: {json.dumps({'content': content})}\n\n"
            # ---------- 流结束后，保存到数据库 ----------
            # async with async_session() as session:
            #     user_msg = ChatMessage(
            #         role="user",
            #         content=request.message,   # 用户消息内容
            #         session_id="default"       # 先固定会话ID
            #     )
            #     session.add(user_msg)
            #     ai_msg = ChatMessage(
            #         role="assistant",
            #         content=full_reply,        # AI完整回复
            #         session_id="default"
            #     )
            #     session.add(ai_msg)
            #     await session.commit()
            # 使用注入的 db 会话
            db.add(ChatMessage(role="user", content=request.message, session_id=request.session_id))
            db.add(ChatMessage(role="assistant", content=full_reply, session_id=request.session_id))
            await db.commit()
            # -
            # 发送结束标志
            # ------------------------------------------
            # 发送结束标志
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            # headers={
            #     "Cache-Control": "no-cache",
            #     "Connection": "keep-alive",
            #     "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲（如果用了）
            # }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/history")
async def get_history(
    session_id: str = "default",
    current_user: User = Depends(get_current_user)
):
    async with async_session() as session:
        from sqlalchemy import select
        stmt = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at)
        result = await session.execute(stmt)
        messages = result.scalars().all()
        return [
            {"role": m.role, "content": m.content, "time": m.created_at.isoformat()}
            for m in messages
        ]

# 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []  # 存放所有连接的客户端

    async def connect(self, websocket: WebSocket):
        await websocket.accept()  # 接受连接
        self.active_connections.append(websocket)  # 加入列表

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)  # 移除

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)  # 给每个客户端发送消息

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # 从 query 参数中获取 token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)  # Policy Violation
        return
    
    # 验证 token
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            await websocket.close(code=1008)
            return
    except:
        await websocket.close(code=1008)
        return
    
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"[{username}] 说: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"[{username}] 离开了")


@app.get("/sessions")
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Session).where(
        Session.user_id == current_user.id
    ).order_by(Session.updated_at.desc())
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return [
        {"id": s.id, "name": s.name, "created_at": s.created_at.isoformat() if s.created_at else None}
        for s in sessions
    ]


@app.post("/sessions")
async def create_session(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session_id = str(uuid4())
    new_session = Session(
        id=session_id,
        name="新对话",
        user_id=current_user.id
    )
    db.add(new_session)
    await db.commit()
    return {"id": session_id, "name": "新对话"}

class UpdateSessionRequest(BaseModel):
    name: str

@app.patch("/sessions/{session_id}")
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Session).where(
        Session.id == session_id,
        Session.user_id == current_user.id
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    session.name = request.name
    await db.commit()
    return {"message": "更新成功"}

@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 先检查会话是否存在且属于当前用户
    stmt = select(Session).where(
        Session.id == session_id,
        Session.user_id == current_user.id
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或无权限删除")
    
    # 删除会话下的所有消息
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    # 删除会话
    await db.execute(delete(Session).where(Session.id == session_id))
    await db.commit()
    return {"message": "会话已删除"}

# 注册
@app.post("/register")
async def register(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await register_user(form_data.username, form_data.password, db)
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# 登录（获取Token）
@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(form_data.username, form_data.password, db)
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def root():
    return {"message": "Backend is running!"}