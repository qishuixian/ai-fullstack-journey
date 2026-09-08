"""
Week 10 Day 1：纯 OpenAI SDK 手写 ReAct Agent
不依赖 LangChain / LangGraph，只用 openai 库实现完整的 Thought→Action→Observation 循环。
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# ---------- 加载环境变量 ----------
load_dotenv()

# ---------- 1. 定义工具函数 ----------

def get_weather(city: str) -> str:
    """获取指定城市的天气（模拟数据）"""
    weather_db = {
        "北京": "晴，25度",
        "上海": "多云，28度",
        "广州": "雷阵雨，30度"
    }
    return weather_db.get(city, f"未知城市：{city}")

def calculator(a: int, b: int) -> int:
    """计算两个整数的乘积"""
    return a * b

# ---------- 2. 工具描述（JSON Schema，符合 OpenAI Function Calling 格式）----------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算两个整数的乘积",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "第一个整数"},
                    "b": {"type": "integer", "description": "第二个整数"}
                },
                "required": ["a", "b"]
            }
        }
    }
]

# 工具名称到实际函数的映射
TOOL_MAP = {
    "get_weather": get_weather,
    "calculator": calculator
}

# ---------- 3. 初始化 OpenAI 客户端 ----------

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
)

MODEL = os.getenv("MODEL_NAME", "deepseek-v4-flash")

# ---------- 4. 工具执行辅助函数 ----------

def execute_tool(name: str, args: dict) -> str:
    """执行工具并返回字符串结果，出错时返回错误信息"""
    func = TOOL_MAP.get(name)
    if not func:
        return f"错误：未知工具 '{name}'"
    try:
        result = func(**args)
        # 确保结果是字符串（OpenAI 要求 tool content 为 string）
        return str(result)
    except Exception as e:
        return f"工具执行失败：{e}"

# ---------- 5. ReAct 主循环 ----------

def react(user_input: str, max_steps: int = 5) -> str:
    """
    纯 OpenAI SDK 实现的 ReAct 循环
    :param user_input: 用户问题
    :param max_steps: 最大推理轮数（熔断）
    :return: 最终回答
    """
    # 初始化消息列表
    messages = [
        {"role": "system", "content": "你是一个有帮助的助手。你可以使用工具获取信息来回答问题。"},
        {"role": "user", "content": user_input}
    ]

    for step in range(max_steps):
        print(f"\n--- 第 {step + 1} 轮推理 ---")

        # 调用 OpenAI API
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0
        )

        choice = response.choices[0]
        msg = choice.message

        # 检查是否有工具调用
        if msg.tool_calls:
            # 将 assistant 消息（含 tool_calls）追加到历史
            assistant_msg = {
                "role": "assistant",
                "content": msg.content,  # 可能为 None
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in msg.tool_calls
                ]
            }
            messages.append(assistant_msg)

            # 逐个执行工具
            for tc in msg.tool_calls:
                func_name = tc.function.name
                func_args = json.loads(tc.function.arguments)  # arguments 是 JSON 字符串
                print(f"  ▶ 调用工具：{func_name}({func_args})")
                result = execute_tool(func_name, func_args)
                print(f"  ✔ 工具结果：{result}")

                # 将工具结果追加为 tool 消息
                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tc.id
                })

            # 继续下一轮循环（让 LLM 根据工具结果进一步推理）
            continue
        else:
            # 没有工具调用，说明 LLM 已给出最终答案
            final_answer = msg.content or ""
            print(f"  ✅ 最终回答：{final_answer}")
            return final_answer

    # 超过最大轮数仍未得到答案
    return "❌ 已达到最大推理次数，无法给出答案。"

# ---------- 6. 主程序入口 ----------

if __name__ == "__main__":
    # 测试用例
    test_questions = [
        "北京天气怎么样？",
        "帮我算 12 乘以 34",
        "上海天气怎么样？再算 56 乘以 78",
        "火星天气怎么样？"  # 测试未知城市
    ]

    for q in test_questions:
        print("\n" + "=" * 60)
        print(f"🤔 用户：{q}")
        answer = react(q)
        print(f"💡 Agent：{answer}")
        print("=" * 60)