import os
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages

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
@tool
def calculator(a: int, b: int) -> int:
    """计算两个整数的乘法"""
    return a * b

@tool
def get_weather(city: str) -> str:
    """查询城市的天气"""
    weather_db = {"北京": "晴，25度", "上海": "多云，28度", "广州": "雷阵雨，30度"}
    return f"{city} 天气：{weather_db.get(city, '未知城市')}"

tools = [calculator, get_weather]
llm_with_tools = llm.bind_tools(tools)

# ==================== 3. 定义状态 ====================
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ==================== 4. 定义节点 ====================
MAX_ITERATIONS = 5

def call_model(state: AgentState):
    ai_messages = [m for m in state["messages"] if isinstance(m, AIMessage)]
    if len(ai_messages) >= MAX_ITERATIONS:
        return {"messages": [AIMessage(content="❌ 已达到最大推理次数，请简化问题。")]}
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

tool_node = ToolNode(tools)

def should_continue(state: AgentState) -> Literal["tools", END]:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END

# ==================== 5. 构建图（⚠️ 不在全局编译，移到 main 内部） ====================
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

# ==================== 6. 测试 ====================
def main():
    print("=== Week 9 Day 5：记忆持久化 + 错误处理 ===\n")
    
    # ✅ 在 with 块内编译并使用 checkpointer
    with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        checkpointer.setup()
        app = workflow.compile(checkpointer=checkpointer)
        
        # 第一次对话
        config = {"configurable": {"thread_id": "session1"}}
        query1 = "我叫小明，帮我算 12 * 34"
        print(f"🤔 用户: {query1}")
        result1 = app.invoke({"messages": [HumanMessage(content=query1)]}, config)
        print(f"💡 Agent: {result1['messages'][-1].content}\n")
        
        # 第二次对话（同一会话）
        query2 = "你还记得我叫什么吗？"
        print(f"🤔 用户: {query2}")
        result2 = app.invoke({"messages": [HumanMessage(content=query2)]}, config)
        print(f"💡 Agent: {result2['messages'][-1].content}\n")
        
        # 第三次对话（新会话）
        config2 = {"configurable": {"thread_id": "session2"}}
        query3 = "你还记得我叫什么吗？"
        print(f"🤔 用户: {query3}（新会话）")
        result3 = app.invoke({"messages": [HumanMessage(content=query3)]}, config2)
        print(f"💡 Agent: {result3['messages'][-1].content}\n")
        
        print("=" * 70)
        print("✅ 记忆持久化验证完成！")

if __name__ == "__main__":
    main()