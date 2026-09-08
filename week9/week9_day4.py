import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode  # ✅ 修复：使用 ToolNode 替代 ToolExecutor
from typing import TypedDict, Literal

# 加载环境变量
load_dotenv()

# ==================== 1. 初始化 LLM ====================
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "deepseek-v4-flash"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://api.deepseek.com"),
    temperature=0,
    max_retries=3,
    timeout=30
)

# ==================== 2. 定义工具 ====================
def calculator(a: int, b: int) -> int:
    """计算两个整数的乘法"""
    print(f"🔧 执行计算器: {a} * {b}")
    return a * b

def get_weather(city: str) -> str:
    """查询城市的天气"""
    print(f"🔧 执行天气查询: {city}")
    # 模拟真实 API 返回
    return f"{city} 天气：晴，25度"

# 工具列表
tools = [calculator, get_weather]

# ==================== 3. 绑定工具给 LLM ====================
llm_with_tools = llm.bind_tools(tools, method="function_calling")

# ==================== 4. 定义状态 ====================
class AgentState(TypedDict):
    messages: list

# ==================== 5. 定义节点 (Node) ====================

def call_model(state: AgentState):
    """LLM 推理节点"""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# ✅ 修复：直接使用 ToolNode 替代手写的 execute_tools
tool_node = ToolNode(tools)

# ==================== 6. 定义条件边 ====================

def should_continue(state: AgentState) -> Literal["tools", END]:
    """路由判断"""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END

# ==================== 7. 构建图 ====================
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)  # ✅ 修复：使用 ToolNode 实例

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

app = workflow.compile()

# ==================== 8. 测试 ====================
def main():
    print("=== Week 9 Day 4：LangGraph 版 ReAct Agent ===\n")
    
    test_inputs = [
        "帮我算一下 12 * 34",
        "北京今天天气怎么样？顺手算下 15 * 6",
    ]
    
    for query in test_inputs:
        print(f"\n🤔 用户提问: {query}")
        print("-" * 80)
        
        initial_state = {"messages": [HumanMessage(content=query)]}
        result = app.invoke(initial_state)
        
        final_answer = result["messages"][-1].content
        print(f"💡 最终答案: {final_answer}")
        print("=" * 120)

if __name__ == "__main__":
    main()