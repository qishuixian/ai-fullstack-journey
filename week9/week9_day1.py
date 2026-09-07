import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==================== 1. 初始化 LLM ====================
def get_llm():
    return ChatOpenAI(
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=0,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )

# ==================== 2. 定义三个工具 ====================
@tool
def calculator(a: int, b: int) -> int:
    """计算两个整数的乘法。"""
    return a * b

@tool
def search_web(query: str) -> str:
    """搜索实时信息（如天气、新闻）。"""
    # 模拟数据，后续可替换为真实 API
    return f"(模拟数据) 关于'{query}'的信息：今天气温25度。"

@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。"""
    return f"(模拟数据) {city}今天晴，气温25度。"

# ==================== 3. 测试 Function Calling ====================
def main():
    print("=== Week 9 Day 1：Function Calling 原理测试 ===\n")
    
    tools = [calculator, search_web, get_weather]
    llm_with_tools = get_llm().bind_tools(tools)
    
    # 测试用例：单个工具调用
    queries = [
        "帮我算一下 12 * 34",
        "搜索一下今天的科技新闻",
        "北京今天天气怎么样？",
        "算一下 56 * 78，顺便查一下上海的天气"  # 多工具调用
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- 测试 {i}：{query} ---")
        response = llm_with_tools.invoke([HumanMessage(content=query)])
        
        print(f"LLM 回复内容: {response.content[:200] if response.content else '(空)'}")
        if hasattr(response, "tool_calls") and response.tool_calls:
            for call in response.tool_calls:
                print(f"  调用工具: {call['name']}, 参数: {call['args']}")
        else:
            print("  (LLM 未调用工具)")
        print("-" * 60)

if __name__ == "__main__":
    main()