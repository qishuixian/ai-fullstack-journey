# -*- coding: utf-8 -*-
import os
from openai import OpenAI   # 调用大模型API
from dotenv import load_dotenv  # 读取.env文件
from fastapi import FastAPI, HTTPException  # Web框架
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

app = FastAPI(title="AI Chat API")

# 允许前端跨域访问（开发阶段需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue 开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求体模型
class ChatRequest(BaseModel):
    message: str

# 对话历史（内存存储，重启会丢失）
# 后续可以换成数据库
history: list[dict] = [
    {"role": "system", "content": "你是一个友善的助手。"}
]

MAX_ROUNDS = 6

@app.post("/chat")
async def chat(req: ChatRequest):
    """非流式接口：接收用户消息，返回 AI 回复"""
    global history

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 添加用户消息
    history.append({"role": "user", "content": req.message})

    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=history,
            temperature=0.7
        )

        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})

        # 截断历史
        while (len(history) - 1) // 2 > MAX_ROUNDS:
            history.pop(1)
            history.pop(1)

        return {"reply": reply}

    except Exception as e:
        # 出错时移除用户消息，保持历史一致
        history.pop()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """健康检查接口"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)