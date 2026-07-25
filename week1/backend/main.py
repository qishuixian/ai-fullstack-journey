# -*- coding: utf-8 -*-
import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

class ChatRequest(BaseModel):
    message: str
    history: list = []  # 历史记录，可选

# ---- 原有的非流式接口（保留用于对比） ----
@app.post("/chat")
async def chat(request: ChatRequest):
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
async def chat_stream(request: ChatRequest):
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
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    # SSE 格式：data: <json>\n\n
                    yield f"data: {json.dumps({'content': content})}\n\n"
            # 发送结束标志
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲（如果用了）
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Backend is running!"}