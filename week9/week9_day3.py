import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 为避免 deepseek-chat 在 2026年7月24日 后被弃用，建议使用新模型名
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-v4-flash")

# ==================== 1. 定义工具 ====================
@tool
def calculator(a: int, b: int) -> int:
    """计算两个整数的乘法。"""
    return a * b

@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。"""
    # 模拟数据，真实场景可接 wttr.in
    weather_data = {
        "北京": "晴，25度",
        "上海": "多云，28度",
        "广州": "雷阵雨，30度",
    }
    return f"{city} 天气：{weather_data.get(city, '未知城市')}"

# 工具字典：用名称快速查找工具
TOOLS = {t.name: t for t in [calculator, get_weather]}

# ==================== 2. 手写 ReAct 循环 ====================
def react_loop(user_query: str, max_iterations: int = 5):
    """
    核心：手写 ReAct Agent 循环
    - user_query: 用户输入
    - max_iterations: 最大循环次数（防止无限循环）
    """
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    llm_with_tools = llm.bind_tools(list(TOOLS.values()))

    # 消息历史：从用户的提问开始
    messages = [HumanMessage(content=user_query)]

    print(f"🤔 用户提问: {user_query}\n{'='*60}")

    for iteration in range(max_iterations):
        print(f"\n--- 第 {iteration + 1} 轮循环 ---")

        # Step 1: Thought（LLM 思考）
        response = llm_with_tools.invoke(messages)
        messages.append(response)  # 把 LLM 的回复加入历史

        # 如果 LLM 没有调用工具 → 说明它已经得出最终答案
        if not response.tool_calls:
            print(f"💡 LLM 最终答案: {response.content}")
            return response.content

        # Step 2: Action（执行工具）
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]

            print(f"🔧 调用工具: {tool_name}, 参数: {tool_args}")

            # 查找并执行工具
            tool_func = TOOLS[tool_name]
            tool_result = tool_func.invoke(tool_args)  # 真正执行函数

            # Step 3: Observation（观察结果）
            # 关键！必须用 ToolMessage 包装结果，并带上 tool_call_id
            observation = ToolMessage(content=str(tool_result), tool_call_id=tool_id)
            messages.append(observation)
            print(f"👁️  工具返回: {tool_result}")

    # 如果循环次数耗尽仍未得出答案
    return "❌ 超过最大循环次数，未能得出最终答案。"


# ==================== 3. 测试 ====================
def main():
    print("=== Week 9 Day 3：手写 ReAct Agent 闭环 ===\n")
    
    test_cases = [
        "帮我算一下 12 * 34",  # 单次工具调用
        "北京今天天气怎么样？顺手算下 15 * 6",  # 多工具 + 需综合回答
    ]
    
    for query in test_cases:
        react_loop(query)
        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()