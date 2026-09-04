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

def get_llm() -> ChatOpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "缺少 DEEPSEEK_API_KEY。请在当前终端先执行 "
            "`$env:DEEPSEEK_API_KEY=\"你的key\"`，或在项目目录创建 .env 文件并写入 "
            "`DEEPSEEK_API_KEY=你的key`。"
        )

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model_name = os.getenv("MODEL_NAME", "deepseek-chat")
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
    )


# 1. 定义工具
@tool
def calculator(expression: str) -> str:
    """评估一个数学表达式。只允许数字和 +, -, *, /, (, )."""
    try:
        # 简单的安全限制，生产环境请用 numexpr 或 sympy
        allowed = set("0123456789+-*/(). ")
        if any(char not in allowed for char in expression):
            return "错误：包含非法字符"
        return str(eval(expression))
    except Exception as exc:
        return f"计算错误: {exc}"


tools = [calculator]


# 2. 定义状态
class AgentState(TypedDict):
    # add_messages 是 LangGraph 的 reducer，会自动把新消息追加到列表中
    messages: Annotated[list, add_messages]


# 3. 定义节点
def agent_node(state: AgentState) -> AgentState:
    """Agent 节点：调用绑定了工具的 LLM。"""
    llm_with_tools = get_llm().bind_tools(tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """路由函数：判断 LLM 是否要求调用工具。"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# 4. 构建图
builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")

builder.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END},
)

builder.add_edge("tools", "agent")

app = builder.compile()


# 5. 运行测试
if __name__ == "__main__":
    print("=== 开始运行 Day 2 ReAct Agent ===")
    inputs = {"messages": [HumanMessage(content="帮我算一下 (1234 * 5678) + 100 等于多少？")]}

    result = app.invoke(inputs)

    print("\n=== 最终对话记录 ===")
    for msg in result["messages"]:
        print(f"[{msg.type}]: {msg.content}")
