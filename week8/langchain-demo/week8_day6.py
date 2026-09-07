import os
import sqlite3
from typing import Annotated, TypedDict, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
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
    iterations: int  # 防死循环计数器

class Route(BaseModel):
    """Supervisor 的路由决策结构（强制约束）"""
    next: Literal["math_agent", "search_agent", "FINISH"] = Field(
        description="下一个要执行的节点，必须是 math_agent, search_agent, 或 FINISH"
    )

# ==================== 3. 定义节点 ====================
# 3.1 Supervisor 节点
def supervisor_node(state: AgentState):
    """主管：看上下文，决定派发任务或结束"""
    # 安全机制：超过 5 次迭代强制结束
    if state.get("iterations", 0) >= 5:
        return {"next": "FINISH", "iterations": state.get("iterations", 0) + 1}
    
    system_prompt = """你是主管。下面有专家：
- math_agent: 仅处理数学计算。
- search_agent: 仅处理实时搜索（如天气）。
以最近一条用户消息为当前任务，不要重新派发历史任务。
如果当前任务已有专家给出答案，或属于闲聊及回顾历史，输出 FINISH。"""
    
    llm = get_llm()
    # DeepSeek 不支持默认的 json_schema，改用工具调用并保留 Route 校验。
    supervisor_llm = llm.with_structured_output(Route, method="function_calling")
    decision = supervisor_llm.invoke(
        [SystemMessage(content=system_prompt)] + state["messages"]
    )
    
    update = {
        "next": decision.next, 
        "iterations": state.get("iterations", 0) + 1
    }
    if decision.next == "FINISH" and isinstance(state["messages"][-1], HumanMessage):
        response = llm.invoke(
            [SystemMessage(content="请根据对话历史回答用户当前的问题。")] + state["messages"]
        )
        update["messages"] = [response]
    return update

# 3.2 Worker 节点（严格限制只干活不调度）
def math_agent(state: AgentState):
    """数学专家：只管算数"""
    agent = create_agent(
        get_llm(), tools=[calculator],
        system_prompt="你是数学专家。处理当前数学任务，整数乘法必须调用 calculator，得到结果后给出答案。",
    )
    result = agent.invoke({"messages": state["messages"]}, {"recursion_limit": 10})
    response = result["messages"][-1]
    return {"messages": [AIMessage(content=f"[数学专家]: {response.content}")]}

def search_agent(state: AgentState):
    """搜索专家：只管查天气"""
    agent = create_agent(
        get_llm(), tools=[search_web],
        system_prompt="你是搜索专家。处理当前搜索任务，必须调用 search_web 后回答，并明确标注工具中的模拟数据。",
    )
    result = agent.invoke({"messages": state["messages"]}, {"recursion_limit": 10})
    response = result["messages"][-1]
    return {"messages": [AIMessage(content=f"[搜索专家]: {response.content}")]}

# ==================== 4. 路由函数 ====================
def router(state: AgentState) -> str:
    return state["next"]

# ==================== 5. 构建图 ====================
builder = StateGraph(AgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("math_agent", math_agent)
builder.add_node("search_agent", search_agent)

builder.add_edge(START, "supervisor")

# 主管的条件路由
builder.add_conditional_edges(
    "supervisor", 
    router, 
    {"math_agent": "math_agent", "search_agent": "search_agent", "FINISH": END}
)

# Worker 干完活必须回主管汇报（形成受控循环）
builder.add_edge("math_agent", "supervisor")
builder.add_edge("search_agent", "supervisor")

# ==================== 6. 记忆持久化 ====================
db_path = os.path.abspath("chat_history.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

app = builder.compile(checkpointer=memory)

# ==================== 7. 运行测试 ====================
if __name__ == "__main__":
    print("=== Day 6：多 Agent 协作测试 (稳定版) ===\n")
    
    config = {"configurable": {"thread_id": "user_day6_v2"}, "recursion_limit": 16}  # 留出 5 轮专家执行及主管终止的步数
    
    print("--- 测试 1：派发给数学专家 ---")
    inputs1 = {"messages": [HumanMessage(content="帮我算一下 12 * 34")], "iterations": 0}
    result1 = app.invoke(inputs1, config)
    for msg in result1["messages"]:
        print(f"[{msg.type}]: {msg.content}")
        
    print("\n--- 测试 2：派发给搜索专家 ---")
    inputs2 = {"messages": [HumanMessage(content="上海今天天气怎么样？")], "iterations": 0}
    result2 = app.invoke(inputs2, config)
    for msg in result2["messages"]:
        print(f"[{msg.type}]: {msg.content}")
        
    print("\n--- 测试 3：结合记忆与闲聊(FINISH) ---")
    inputs3 = {"messages": [HumanMessage(content="我叫小明，刚才让我算了什么？")], "iterations": 0}
    result3 = app.invoke(inputs3, config)
    for msg in result3["messages"]:
        print(f"[{msg.type}]: {msg.content}")
