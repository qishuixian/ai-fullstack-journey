import os
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

# 加载环境变量
load_dotenv()

# ==================== LLM 初始化 ====================
def get_llm():
    return ChatOpenAI(
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=0,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )

# ==================== 工具定义（升级版） ====================
@tool
def calculator(a: int, b: int) -> int:
    """计算两个整数的乘法。"""
    return a * b

@tool
def search_web(query: str) -> str:
    """搜索实时信息（如新闻）。"""
    # Day 2：暂时保留模拟数据，后续可替换为 Tavily/Sing Search 等真实 API
    return f"(模拟搜索结果) 关于'{query}'的最新信息：暂无实时数据。"

@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。"""
    # Day 2 升级：接入免费天气 API wttr.in
    try:
        # %C 代表天气状况（如晴天/多云），%t 代表温度
        url = f"https://wttr.in/{city}?format=%C+%t"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return f"{city} 当前天气：{resp.text}"
        else:
            return f"(模拟降级) {city} 今天晴，气温25度。"
    except Exception:
        return f"(模拟降级) {city} 今天晴，气温25度。"

# ==================== 测试多工具决策 ====================
def main():
    print("=== Week 9 Day 2：升级真实天气 API 与多工具决策测试 ===\n")
    
    tools = [calculator, search_web, get_weather]
    llm_with_tools = get_llm().bind_tools(tools)
    
    test_cases = [
        "帮我算一下 12 * 34",
        "北京今天天气怎么样？",
        "算一下 56 * 78，顺便查一下上海的天气",
        "查一下广州的天气，再搜一下今天的AI新闻，最后算一下 100 * 200"  # 极端多工具测试
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}：{query} ---")
        response = llm_with_tools.invoke([HumanMessage(content=query)])
        
        print(f"LLM 思考/回复: {response.content[:200] if response.content else '(空)'}")
        if hasattr(response, "tool_calls") and response.tool_calls:
            for call in response.tool_calls:
                print(f"  👉 调用工具: {call['name']}, 参数: {call['args']}")
        else:
            print("  (LLM 未调用工具)")
        print("-" * 60)

if __name__ == "__main__":
    main()