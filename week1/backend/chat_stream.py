# -*- coding: utf-8 -*-
import os
from openai import OpenAI
from dotenv import load_dotenv
# 加载 .env 里的密钥
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 系统提示词 + 对话历史
messages = [
    {"role": "system", "content": "你是一个友善的助手。"}
]

print("🤖 AI 助手已启动，输入 'quit' 退出")
print("-" * 40)

while True:
    user_input = input("你: ")
    if user_input.lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})
    # 流式调用，设置stream=True，返回一个生成器
    stream = client.chat.completions.create(
        model="deepseek-chat",  # 如果报错说模型弃用，改用 deepseek-v4-flash
        messages=messages,
        temperature=0.7,
        stream=True,  # 设置流式调用，返回一个生成器
        # max_tokens=1000,  # 设置最大返回字符数
    )
    print("AI: ", end="", flush=True)  # 不换行输出

    full_reply = ""
    for chunk in stream :
        if chunk.choices and chunk.choices[0].delta:
            content  = chunk.choices[0].delta.content
            print(content, end="", flush=True)  # 逐字打印
            full_reply += content   # 去除末尾的空格

    print("\n")  # 换行
    messages.append({"role": "assistant", "content": full_reply})

print("再见！")