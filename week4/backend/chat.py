import os
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 里的密钥
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 发一条消息给 AI
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个友善的助手。"},
        {"role": "user", "content": "用一句话介绍什么是RAG"}
    ],
    temperature=0.7
)

# 打印回复
print(response.choices[0].message.content)