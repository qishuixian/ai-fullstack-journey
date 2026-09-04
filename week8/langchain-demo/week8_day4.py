import os
import sys
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI  # 虽然叫 ChatOpenAI，但实际连 DeepSeek
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.errors import GraphRecursionError

# 加载环境变量
load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==================== 1. 初始化 DeepSeek LLM ====================
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "deepseek-chat"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    temperature=0,
)

# ==================== 2. 定义工具 ====================
@tool
def calculator(expression: str) -> str:
    """计算数学表达式。输入如 '123 * 456'。"""
    try:
        allowed = set("0123456789+-*/(). ")
        if any(char not in allowed for char in expression):
            return "错误：包含非法字符"
        return str(eval(expression))
    except Exception as exc:
        return f"计算错误: {exc}"

@tool
def search_web(query: str) -> str:
    """模拟搜索网页，返回假数据。"""
    return f"搜索结果：关于'{query}'的最新信息是：(假数据) 今天气温 25 度。"

calc_tools = [calculator]
search_tools = [search_web]

# ==================== 3. 定义状态 ====================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next: Annotated[str, lambda x, y: y]   # 记录下一步去向

# ==================== 4. 定义节点 ====================

# --- 改造点 1：使用工具调用的主管路由（兼容 DeepSeek）---
def supervisor_node(state: AgentState) -> dict:
    """主管节点：通过工具调用决定下一步"""
    
    # 如果最后一条是工具结果，说明子任务完成，直接总结
    if state["messages"][-1].type == "tool":
        response = llm.invoke(state["messages"] + [HumanMessage(content="请根据工具结果总结回答用户。")])
        return {"messages": [response]}
    
    # 给主管绑定一个路由工具，强制它通过工具调用来输出路由决策
    @tool
    def route(next_step: str) -> str:
        """选择下一个要执行的角色。可选值：'calc'（计算）, 'search'（搜索）, 'end'（结束）。"""
        return next_step
    
    # 绑定路由工具，并设置 tool_choice 强制调用
    supervisor_llm = llm.bind_tools([route], tool_choice="route")
    
    prompt = HumanMessage(content="你是主管。根据用户输入决定下一步：需要计算选 'calc'，需要搜索选 'search'，如果可以直接回答或已完成选 'end'。请调用 route 工具做出选择。")
    
    response = supervisor_llm.invoke(state["messages"] + [prompt])
    
    # 提取工具调用参数
    if hasattr(response, "tool_calls") and response.tool_calls:
        next_value = response.tool_calls[0]["args"]["next_step"]
        return {"next": next_value}
    else:
        # 如果模型没有调用工具，默认结束（防止死循环）
        return {"next": "end"}

def calc_agent_node(state: AgentState) -> dict:
    """计算专员"""
    llm_with_tools = llm.bind_tools(calc_tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def search_agent_node(state: AgentState) -> dict:
    """搜索专员"""
    llm_with_tools = llm.bind_tools(search_tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# ==================== 5. 构建图 ====================
builder = StateGraph(AgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("calc", calc_agent_node)
builder.add_node("search", search_agent_node)
builder.add_node("calc_tools", ToolNode(calc_tools))
builder.add_node("search_tools", ToolNode(search_tools))

builder.add_edge(START, "supervisor")

builder.add_conditional_edges(
    "supervisor",
    lambda state: state["next"],
    {"calc": "calc", "search": "search", "end": END}
)

builder.add_edge("calc", "calc_tools")
builder.add_edge("search", "search_tools")
builder.add_edge("calc_tools", "supervisor")
builder.add_edge("search_tools", "supervisor")

# --- 改造点 2：编译时设置递归限制 ---
app = builder.compile()

# ==================== 6. 运行测试 ====================
if __name__ == "__main__":
    print("=== 开始运行 Day 4 Multi-Agent (DeepSeek 版) ===")
    
    # 测试搜索
    inputs = {"messages": [HumanMessage(content="今天天气怎么样？")]}
    
    try:
        # 运行时设置递归限制（公式：2 * 预期最大迭代次数 + 1）
        result = app.invoke(inputs, {"recursion_limit": 7})
        
        print("\n=== 最终对话记录 ===")
        for msg in result["messages"]:
            print(f"[{msg.type}]: {msg.content}")
            
    except GraphRecursionError:
        print("❌ Agent 达到最大迭代次数，已停止（防止死循环烧钱）")