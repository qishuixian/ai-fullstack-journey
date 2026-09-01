import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# 1. 定义工具（复用 Day 1，新增 RAG 搜索工具）
@tool
def get_weather(city: str) -> str:
    """输入城市名称，返回该城市的当前天气。"""
    return f"{city} 今天是晴天，25度。"


@tool
def calculate_multiply(a: int, b: int) -> int:
    """计算两个整数的乘积。"""
    return a * b


@tool
def search_rag_knowledge_base(query: str) -> str:
    """搜索本地 RAG 知识库。用于查询历史文档、个人笔记或专有知识。"""
    # 实际项目中这里会调用向量数据库检索
    print(f"[调试] 执行了 RAG 搜索工具，查询: {query}")
    return f"RAG 检索结果：关于'{query}'的文档片段..."


tools = [get_weather, calculate_multiply, search_rag_knowledge_base]


def build_agent():
    """创建兼容 LangChain 1.x 的工具调用 Agent。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "缺少 DEEPSEEK_API_KEY。请在当前终端先执行 "
            "`$env:DEEPSEEK_API_KEY=\"你的key\"`，或在项目目录创建 .env 文件并写入 "
            "`DEEPSEEK_API_KEY=你的key`。"
        )

    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt="你是一个全栈开发专家助手。你可以使用工具来回答问题。如果不需要工具，请直接回答。",
    )


def extract_final_answer(result: dict) -> str:
    """从 LangChain 1.x agent 返回值中取出最后一条 AI 回复。"""
    messages = result.get("messages", [])
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            return str(message.content)
    return "未获取到最终回答。"


# 7. 运行测试
def run_day2():
    print("--- Day 2: 框架编排 Agent 测试 ---")
    agent = build_agent()
    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "广州天气怎么样？另外帮我算 12 * 5，并查一下我的 RAG 笔记里关于 LangGraph 的内容。",
                }
            ]
        },
        config={"recursion_limit": 5},
    )
    print("最终回答:", extract_final_answer(response))


if __name__ == "__main__":
    run_day2()
