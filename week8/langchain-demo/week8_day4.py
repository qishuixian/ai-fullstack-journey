import os
import json
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Literal
import operator

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

# ==================== 0. 环境初始化 ====================
load_dotenv()

# 使用 DeepSeek 兼容 OpenAI 格式
llm = ChatOpenAI(
    model="deepseek-chat", 
    temperature=0,
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ==================== 1. 定义工具 ====================
@tool
def calculator(a: int, b: int) -> int:
    """计算两个整数的乘法。"""
    return a * b

@tool
def search_web(query: str) -> str:
    """搜索实时信息（如天气）。"""
    # 模拟假数据
    return f"(假数据) 今天气温 25 度。"

calc_tools = [calculator]
search_tools = [search_web]

# ==================== 2. 定义状态 ====================
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    next: str 
    iterations: int # 熔断计数器

# ==================== 3. 定义节点 ====================
def supervisor_node(state: AgentState) -> dict:
    """主管节点：决定下一步（宽松匹配版）"""
    # 计数器兜底防死循环
    if state.get("iterations", 0) > 3:
        return {"next": "end", "messages": [AIMessage(content="达到最大迭代次数，强制结束")]}
        
    last_message = state["messages"][-1]
    
    # 如果是工具返回的结果，直接总结
    if isinstance(last_message, ToolMessage):
        response = llm.invoke(state["messages"] + [HumanMessage(content="请根据工具结果总结回答用户。")])
        return {"messages": [response], "next": "end"}
    
    # 不使用工具调用，直接让模型思考并输出文本
    prompt = HumanMessage(content="""你是主管。分析用户需求：
            - 如果需要计算数学题，你的回复必须包含关键字 calc。
            - 如果需要搜索信息（如天气），你的回复必须包含关键字 search。
            - 如果可以直接回答或任务已完成，回复 end。

            用户当前输入和历史记录如上，请做出决定。""")
    
    response = llm.invoke(state["messages"] + [prompt])
    content = response.content.lower() # 转小写匹配
    
    # 宽松匹配逻辑
    if "calc" in content:
        next_value = "calc"
    elif "search" in content:
        next_value = "search"
    else:
        next_value = "end"
        
    return {
        "next": next_value, 
        "messages": [response], 
        "iterations": state.get("iterations", 0) + 1
    }
def calc_agent_node(state: AgentState) -> dict:
    """计算专员：绑定计算工具"""
    llm_with_tools = llm.bind_tools(calc_tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def search_agent_node(state: AgentState) -> dict:
    """搜索专员：绑定搜索工具"""
    llm_with_tools = llm.bind_tools(search_tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# 自定义工具执行节点：确保正确返回 ToolMessage 并打上防污染标记
def custom_tool_node(state: AgentState) -> dict:
    """显式执行工具并封装为 ToolMessage"""
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {}
        
    tool_messages = []
    for tc in last_message.tool_calls:
        # 简单执行工具
        if tc["name"] == "calculator":
            res = calculator.invoke(tc["args"])
        elif tc["name"] == "search_web":
            res = search_web.invoke(tc["args"])
        else:
            res = "未知工具"
            
        # 封装为标准 ToolMessage，并加入特征标记防止模型误判为新的指令
        tool_messages.append(
            ToolMessage(
                content=f"__agent_result__ {res}", 
                tool_call_id=tc["id"]
            )
        )
    return {"messages": tool_messages}

# ==================== 4. 构建图 ====================
builder = StateGraph(AgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("calc", calc_agent_node)
builder.add_node("search", search_agent_node)
builder.add_node("tools", custom_tool_node) # 使用自定义工具节点

builder.add_edge(START, "supervisor")

# 主管路由
builder.add_conditional_edges(
    "supervisor",
    lambda state: state["next"],
    {"calc": "calc", "search": "search", "end": END}
)

# 子Agent调用工具判断
def check_tool_calls(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

builder.add_conditional_edges("calc", check_tool_calls, {"tools": "tools", END: END})
builder.add_conditional_edges("search", check_tool_calls, {"tools": "tools", END: END})

# 工具执行完强制回到主管复盘
builder.add_edge("tools", "supervisor")

app = builder.compile()

# ==================== 5. 运行测试 ====================
if __name__ == "__main__":
    print("=== 开始运行 Day 4 Multi-Agent (DeepSeek 终极稳定版) ===")
    
    inputs = {
        "messages": [HumanMessage(content="今天天气怎么样？顺便算下 123 * 456")], 
        "iterations": 0
    }
    
    try:
        # 保留底层递归限制作为最后一道防线
        result = app.invoke(inputs, {"recursion_limit": 10})
        
        print("\n=== 最终对话记录 ===")
        for msg in result["messages"]:
            print(f"[{msg.type}]: {msg.content}")
            
    except Exception as e:
        print(f"❌ 捕获到异常（已熔断）: {e}")