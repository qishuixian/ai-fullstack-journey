import os
import sys
import sqlite3
from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode

import operator

load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def get_llm() -> ChatOpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "缺少 DEEPSEEK_API_KEY。请在当前终端先执行 "
            "`$env:DEEPSEEK_API_KEY=\"你的key\"`，或在项目目录创建 .env 文件并写入 "
            "`DEEPSEEK_API_KEY=你的key`。"
        )

    return ChatOpenAI(
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=0,
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )

# ==================== 1. 定义工具 ====================
@tool
def calculator(a: int, b: int) -> int:
    """计算两个整数的乘法。"""
    return a * b

@tool
def search_web(query: str) -> str:
    """搜索实时信息（如天气）。"""
    return f"(假数据) 关于'{query}'的信息：今天气温25度。"

tools = [calculator, search_web]
tool_node = ToolNode(tools)

# ==================== 2. 定义状态 ====================
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    next: str

# ==================== 3. 定义节点 ====================
def agent_node(state: AgentState) -> dict:
    """单一 Agent 节点（简化版，专注演示记忆）"""
    llm_with_tools = get_llm().bind_tools(tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def router(state: AgentState) -> str:
    """判断是否需要调用工具"""
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return END

# ==================== 4. 构建图 ====================
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", router, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

# ==================== 5. 选择记忆后端 ====================
# 方案 A：内存记忆（MemorySaver）
#memory = MemorySaver()  

# 方案 B：SQLite 持久化记忆（取消下面注释即可启用）
db_path = os.path.abspath("chat_history.db")
conn = sqlite3.connect(db_path, check_same_thread=False)  # [5,7](@ref)
memory = SqliteSaver(conn)

app = builder.compile(checkpointer=memory)

# ==================== 6. 运行测试 ====================
if __name__ == "__main__":
    print("=== Day 5：长期记忆测试 ===\n")
    
    # 第一次对话
    config = {"configurable": {"thread_id": "user_001"}}  # 会话ID
    inputs = {"messages": [HumanMessage(content="我叫小明，帮我算一下 12 * 34")]}
    result = app.invoke(inputs, config)
    print("--- 第一轮对话 ---")
    for msg in result["messages"]:
        print(f"[{msg.type}]: {msg.content}")
    
    print("\n--- 第二轮对话（同一会话，Agent 记得我叫小明）---")
    inputs2 = {"messages": [HumanMessage(content="你还记得我的名字吗？")]}
    result2 = app.invoke(inputs2, config)
    for msg in result2["messages"]:
        print(f"[{msg.type}]: {msg.content}")
    
    print("\n--- 第三轮对话（不同会话ID，Agent 不记得我）---")
    config2 = {"configurable": {"thread_id": "user_002"}}
    inputs3 = {"messages": [HumanMessage(content="你还记得我的名字吗？")]}
    result3 = app.invoke(inputs3, config2)
    for msg in result3["messages"]:
        print(f"[{msg.type}]: {msg.content}")
