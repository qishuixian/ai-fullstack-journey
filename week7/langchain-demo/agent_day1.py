from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import sys

load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
# ---------------------------------------------------------
# 1. 工具定义（使用 @tool 装饰器）
# 模型靠函数的 docstring 来决定何时调用该工具
# ---------------------------------------------------------
@tool
def get_weather(city: str) -> str:
    """输入城市名称，返回该城市的当前天气。"""
    # 实际项目中这里会调用第三方天气 API
    return f"{city} 今天是晴天，25度。"

@tool
def calculate_multiply(a: int, b: int) -> int:
    """将两个数字相乘。"""
    return a * b

tools = [get_weather, calculate_multiply]


def build_llm():
    """创建模型实例，并在缺少凭证时给出清晰提示。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "缺少 DEEPSEEK_API_KEY。请在当前终端先执行 "
            "`$env:DEEPSEEK_API_KEY=\"你的key\"`，或在项目目录创建 .env 文件并写入 "
            "`DEEPSEEK_API_KEY=你的key`。"
        )

    # 提示：这里以 DeepSeek 为例，你可以替换成 GPT-4o 等支持工具调用的模型
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    return llm.bind_tools(tools)  # 把工具“绑”给模型，让它知道手里有什么武器[1,3](@ref)

# ---------------------------------------------------------
# 3. ReAct 编排循环（简化版）
# ---------------------------------------------------------
def run_agent(user_query: str):
    print(f"用户: {user_query}")
    messages = [HumanMessage(content=user_query)]
    llm_with_tools = build_llm()
    
    # 设置最大循环次数，防止 Agent 陷入死循环[6](@ref)
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        # 让模型思考并决定下一步
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        
        # 检查模型是否决定调用工具
        if not response.tool_calls:
            # 如果没有调用工具，说明模型给出了最终答案
            print(f"Agent 最终回答: {response.content}")
            break
            
        # 执行工具调用
        for tool_call in response.tool_calls:
            print(f"Agent 思考: 决定调用工具 [{tool_call['name']}]，参数: {tool_call['args']}")
            
            # 找到对应的工具并执行
            try:
                selected_tool = {"get_weather": get_weather, "calculate_multiply": calculate_multiply}[tool_call["name"]]
                tool_result = selected_tool.invoke(tool_call["args"])
                print(f"工具执行结果: {tool_result}")
                
                # 将工具结果包装成 ToolMessage 交还给模型[3](@ref)
                messages.append(ToolMessage(content=tool_result, tool_call_id=tool_call["id"]))
            except Exception as e:
                # 踩坑预警：工具报错一定要捕获并反馈给模型，不要让程序崩溃[6](@ref)
                messages.append(ToolMessage(content=f"工具执行报错: {str(e)}", tool_call_id=tool_call["id"]))

if __name__ == "__main__":
    run_agent("广州今天天气怎么样？另外帮我算一下 12 乘以 5 等于多少？")
