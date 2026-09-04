import os
import sqlite3
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

# 初始化 DeepSeek LLM
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "deepseek-chat"),
    temperature=0,
    api_key=os.getenv("DEEPSEEK_API_KEY"),
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

# ==================== 2. 定义状态 ====================
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # 使用官方 reducer 追加消息
    next: str  # Supervisor 的路由决策

# ==================== 3. 定义 Worker Agents (下属) ====================
def math_agent(state: AgentState) -> dict:
    """数学专家 Agent"""
    user_msg = state['messages'][-1].content
    response = llm.invoke([
        SystemMessage(content="你是数学专家，只负责计算。"),
        HumanMessage(content=user_msg)
    ])
    return {"messages": [AIMessage(content=f"[数学专家]: {response.content}")]}

def search_agent(state: AgentState) -> dict:
    """搜索专家 Agent"""
    user_msg = state['messages'][-1].content
    response = llm.invoke([
        SystemMessage(content="你是搜索专家，负责查天气等实时信息。"),
        HumanMessage(content=user_msg)
    ])
    return {"messages": [AIMessage(content=f"[搜索专家]: {response.content}")]}

# ==================== 4. 定义 Supervisor (主管) ====================
def supervisor(state: AgentState) -> dict:
    """主管 Agent：决定派发任务给谁"""
    system_prompt = """你是团队主管。根据用户输入决定派发任务：
    - 如果涉及数字计算/乘法，派发给 math_agent
    - 如果涉及天气/实时搜索，派发给 search_agent
    - 如果只是闲聊或已经完成，输出 FINISH
    请只输出目标名称(math_agent, search_agent, 或 FINISH)。"""
    
    # 把历史消息传给主管看
    messages = [SystemMessage(content=system_prompt)] + state['messages']
    response = llm.invoke(messages)
    decision = response.content.strip().lower()
    
    if "math" in decision: return {"next": "math_agent"}
    if "search" in decision: return {"next": "search_agent"}
    return {"next": "FINISH"}

# ==================== 5. 构建图 ====================
builder = StateGraph(AgentState)

# 添加节点
builder.add_node("supervisor", supervisor)
builder.add_node("math_agent", math_agent)
builder.add_node("search_agent", search_agent)

# 设置入口
builder.add_edge(START, "supervisor")

# 主管的条件路由
builder.add_conditional_edges(
    "supervisor", 
    lambda s: s["next"],  # 读取 state 里的 next 字段决定去向
    {
        "math_agent": "math_agent",
        "search_agent": "search_agent",
        "FINISH": END
    }
)

# Worker 干完活后，必须回到主管那里汇报（形成循环）
builder.add_edge("math_agent", "supervisor")
builder.add_edge("search_agent", "supervisor")

# ==================== 6. 记忆持久化 ====================
db_path = os.path.abspath("chat_history.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

app = builder.compile(checkpointer=memory)

# ==================== 7. 运行测试 ====================
if __name__ == "__main__":
    print("=== Day 6：多 Agent 协作测试 ===\n")
    
    config = {"configurable": {"thread_id": "user_day6"}}  # 会话ID
    
    # 测试 1：数学任务
    print("--- 测试 1：派发给数学专家 ---")
    inputs1 = {"messages": [HumanMessage(content="帮我算一下 12 * 34")]}
    result1 = app.invoke(inputs1, config)
    for msg in result1["messages"]:
        print(f"[{msg.type}]: {msg.content}")
        
    # 测试 2：搜索任务
    print("\n--- 测试 2：派发给搜索专家 ---")
    inputs2 = {"messages": [HumanMessage(content="上海今天天气怎么样？")]}
    result2 = app.invoke(inputs2, config)
    for msg in result2["messages"]:
        print(f"[{msg.type}]: {msg.content}")
        
    # 测试 3：结合记忆的闲聊
    print("\n--- 测试 3：结合记忆与闲聊(FINISH) ---")
    inputs3 = {"messages": [HumanMessage(content="我叫小明，刚才让我算了什么？")]}
    result3 = app.invoke(inputs3, config)
    for msg in result3["messages"]:
        print(f"[{msg.type}]: {msg.content}")