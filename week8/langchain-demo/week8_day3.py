import os
import sys
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# 加载环境变量
load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==================== 1. 定义 LLM ====================
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "deepseek-chat"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    temperature=0,
)

# ==================== 2. 定义工具 ====================
@tool
def calculator(expression: str) -> str:
    """评估一个数学表达式。只允许数字和 +, -, *, /, (, )."""
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

# ==================== 3. 定义状态（必须放在节点函数之前） ====================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next: Annotated[str, lambda x, y: y]   # 记录下一步去向

# ==================== 4. 定义节点函数 ====================
def supervisor_node(state: AgentState) -> dict:
    """主管节点：决定下一个步骤"""
    last_message = state["messages"][-1]
    
    # 如果最后一条消息是工具返回的结果，说明子 agent 已经干完活，主管直接总结
    if last_message.type == "tool":
        response = llm.invoke(state["messages"] + [HumanMessage(content="请根据工具结果总结回答用户。")])
        return {"messages": [response]}
        
    # 否则，主管思考该派发给谁
    response = llm.invoke(
        state["messages"] + 
        [HumanMessage(content="你是主管。请决定下一步：如果需要计算选 'calc'，需要搜索选 'search'，如果可以直接回答或已完成任务选 'end'。")]
    )
    
    # 简单解析主管的回复来决定路由
    content = response.content.lower()
    if "calc" in content:
        return {"next": "calc"}
    elif "search" in content:
        return {"next": "search"}
    else:
        return {"next": "end"}

def calc_agent_node(state: AgentState) -> dict:
    """计算专员：只处理计算任务"""
    llm_with_tools = llm.bind_tools(calc_tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def search_agent_node(state: AgentState) -> dict:
    """搜索专员：只处理搜索任务"""
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

app = builder.compile()

# ==================== 6. 运行测试 ====================
if __name__ == "__main__":
    print("=== 开始运行 Day 3 Multi-Agent ===")
    
    # 测试计算
    inputs = {"messages": [HumanMessage(content="帮我算一下 123 * 456 等于多少？")]}
    result = app.invoke(inputs)
    
    print("\n=== 最终对话记录 (计算测试) ===")
    for msg in result["messages"]:
        print(f"[{msg.type}]: {msg.content}")
        
    # 测试搜索
    inputs2 = {"messages": [HumanMessage(content="今天天气怎么样？")]}
    result2 = app.invoke(inputs2)
    
    print("\n=== 最终对话记录 (搜索测试) ===")
    for msg in result2["messages"]:
        print(f"[{msg.type}]: {msg.content}")