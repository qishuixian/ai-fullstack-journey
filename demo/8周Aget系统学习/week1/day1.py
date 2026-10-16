import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

resp = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "deepseek-chat"),
    temperature=0.3,      # 低温，偏稳定
    max_tokens=500,        # 限制输出长度，控成本
    messages=[
        {"role": "system", "content": "你是用大白话讲技术的助手，回答简洁。"},
        {"role": "user", "content": "用前端ajax类比解释什么是大模型API"},
    ],
)

print(resp.choices[0].message.content)
print("用量:", resp.usage)