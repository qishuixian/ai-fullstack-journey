# -*- coding: utf-8 -*-
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 系统提示词（不计入轮数限制）
system_message = {"role": "system", "content": "你是一个友善的助手。"}

# 最大保留的对话轮数（用户+助手为一轮）
MAX_ROUNDS = 6

# 对话历史（初始只包含 system message）
messages = [system_message]

print("🤖 AI 助手（管理版）已启动")
print("命令: /reset 清空历史 | /stats 查看统计 | quit 退出")
print("-" * 40)

total_input_tokens = 0
total_output_tokens = 0

while True:
    user_input = input("你: ")
    
    # 处理特殊命令
    if user_input.lower() == "quit":
        break
    elif user_input.lower() == "/reset":
        messages = [system_message]
        print("🔄 对话历史已清空\n")
        continue
    elif user_input.lower() == "/stats":
        print(f"📊 总输入 Token: {total_input_tokens}")
        print(f"📊 总输出 Token: {total_output_tokens}")
        print(f"💰 预估费用: {(total_input_tokens + total_output_tokens) * 0.000002:.4f} 元")
        print(f"💬 当前历史轮数: {(len(messages)-1)//2}\n")
        continue

    # 添加用户消息
    messages.append({"role": "user", "content": user_input})

    # 调用 API（流式）
    try:
        stream = client.chat.completions.create(
            model="deepseek-v4-flash",  # 使用最新模型
            messages=messages,
            temperature=0.7,
            stream=True,
            stream_options={"include_usage": True}  # 启用用量统计（需要SDK支持）
        )
    except Exception as e:
        print(f"❌ API 调用失败: {e}")
        # 移除刚才添加的用户消息，恢复状态
        messages.pop()
        continue

    print("AI: ", end="", flush=True)
    full_reply = ""
    usage = None

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_reply += content
        
        # 收集用量信息（最后一个 chunk 可能携带）
        if hasattr(chunk, 'usage') and chunk.usage:
            usage = chunk.usage

    print("\n")

    # 如果没有从流中获取到 usage，尝试从响应中获取（备用）
    if usage:
        total_input_tokens += usage.prompt_tokens
        total_output_tokens += usage.completion_tokens
    else:
        # 估算：粗略按字符数估算，仅作参考
        est_input = len(user_input) * 2
        est_output = len(full_reply) * 2
        total_input_tokens += est_input
        total_output_tokens += est_output

    # 添加助手回复
    messages.append({"role": "assistant", "content": full_reply})

    # 限制历史轮数：保留 system + 最近 MAX_ROUNDS 轮
    # 轮数 = (len(messages) - 1) / 2，因为每轮用户+助手两条消息
    while (len(messages) - 1) // 2 > MAX_ROUNDS:
        # 删除最早的一轮（用户+助手两条）
        messages.pop(1)  # 第一条用户消息
        messages.pop(1)  # 对应的助手消息

print("再见！")