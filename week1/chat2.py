import os
from openai import OpenAI
from dotenv import load_dotenv

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

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.7
    )

    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})

    print(f"AI: {reply}\n")

print("再见！")