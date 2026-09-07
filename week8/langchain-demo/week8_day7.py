import os
import sqlite3
from typing import Annotated, TypedDict, Literal, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.types import Send
from langgraph.checkpoint.sqlite import SqliteSaver

import operator

load_dotenv()
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==================== 0. 初始化 LLM ====================
def get_llm():
    return ChatOpenAI(
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=0,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        max_retries=3,
        request_timeout=30,
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

# ==================== 2. 定义状态与路由结构 ====================
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    next: str
    iterations: int

class Route(BaseModel):
    """Supervisor 的路由决策结构"""
    next: Literal["math_agent", "search_agent", "both", "FINISH"] = Field(
        description="下一个要执行的节点"
    )

# ==================== 3. 定义节点 ====================
def supervisor_node(state: AgentState):
    """主管：决定派发任务（支持并行）"""
    if state.get("iterations", 0) >= 5:
        return {"next": "FINISH", "iterations": state.get("iterations", 0) + 1}
    
    system_prompt = """你是主管。下面有专家：
- math_agent: 处理数学计算。
- search_agent: 处理实时搜索。
如果用户的当前问题同时包含数学和搜索需求，输出 'both'。
如果只需数学，输出 'math_agent'。
如果只需搜索，输出 'search_agent'。
如果是闲聊或回顾，输出 'FINISH'。"""
    
    llm = get_llm()
    supervisor_llm = llm.with_structured_output(Route, method="function_calling")
    decision = supervisor_llm.invoke(
        [SystemMessage(content=system_prompt)] + state["messages"]
    )
    
    return {
        "next": decision.next, 
        "iterations": state.get("iterations", 0) + 1
    }

def math_agent(state: AgentState):
    """数学专家"""
    agent = create_agent(
        get_llm(),
        tools=[calculator],
        system_prompt="你是数学专家。只处理数学任务，整数乘法必须调用 calculator。",
    )
    result = agent.invoke({"messages": state["messages"]}, {"recursion_limit": 10})
    response = result["messages"][-1]
    return {"messages": [AIMessage(content=f"[数学专家]: {response.content}")]}

def search_agent(state: AgentState):
    """搜索专家"""
    agent = create_agent(
        get_llm(),
        tools=[search_web],
        system_prompt="你是搜索专家。只处理搜索任务，必须调用 search_web，并说明结果是模拟数据。",
    )
    result = agent.invoke({"messages": state["messages"]}, {"recursion_limit": 10})
    response = result["messages"][-1]
    return {"messages": [AIMessage(content=f"[搜索专家]: {response.content}")]}

def synthesizer_node(state: AgentState):
    """汇总节点：合并并行结果"""
    llm = get_llm()
    response = llm.invoke(
        [SystemMessage(content="请汇总以下专家的结果，给用户一个最终回复：")] + state["messages"]
    )
    return {"messages": [response], "next": "FINISH"}

# ==================== 4. 路由逻辑 ====================
def router(state: AgentState):
    return state["next"]

def parallel_router(state: AgentState):
    """并行路由：如果决策是 both，同时发送给两个专家"""
    if state["next"] == "both":
        # 使用 Send 实现动态分发（并发执行）
        return [Send("math_agent", state), Send("search_agent", state)]
    return state["next"]

# ==================== 5. 构建图 ====================
builder = StateGraph(AgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("math_agent", math_agent)
builder.add_node("search_agent", search_agent)
builder.add_node("synthesizer", synthesizer_node)

builder.add_edge(START, "supervisor")

# 主管的条件路由（包含并行分支）
builder.add_conditional_edges(
    "supervisor", 
    parallel_router, 
    {
        "math_agent": "math_agent",
        "search_agent": "search_agent",
        "FINISH": END
    }
)

# 专家干完活后去汇总
builder.add_edge(["math_agent", "search_agent"], "synthesizer")
builder.add_edge("synthesizer", END)

# ==================== 6. 记忆持久化 ====================
db_path = os.path.abspath("chat_history.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

app = builder.compile(checkpointer=memory)

# ==================== 7. 运行测试 ====================
if __name__ == "__main__":
    print("=== Day 7：并行执行测试 ===\n")
    
    config = {"configurable": {"thread_id": "user_day7_v2"}, "recursion_limit": 16}
    
    print("--- 测试：同时派发数学和搜索任务 ---")
    inputs = {"messages": [HumanMessage(content="帮我算一下 12 * 34，同时查一下上海天气")], "iterations": 0}
    result = app.invoke(inputs, config)
    
    for msg in result["messages"]:
        print(f"[{msg.type}]: {msg.content}")
