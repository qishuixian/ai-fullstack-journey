import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

# 加载环境变量
load_dotenv()

# 1. 初始化模型
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0
)

# 2. 定义工具（使用 @tool 装饰器）
@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气。"""
    if city == "火星":
        return "未知城市：火星"
    if city == "北京":
        return "北京 天气：晴，25度"
    return f"{city} 天气：多云，20度"

@tool
def calculator(a: int, b: int) -> int:
    """计算两个整数的乘积。"""
    return a * b

# 工具列表与映射
tools = [get_weather, calculator]
tool_map = {tool.name: tool for tool in tools}

# 3. ReAct 主循环（手写）
def react(user_input: str, max_steps: int = 5) -> str:
    # 使用 LangChain 原生消息类
    messages = [
        SystemMessage(content="你是一个有帮助的助手。你可以使用工具获取信息。"),
        HumanMessage(content=user_input)
    ]
    
    # 绑定工具到模型
    llm_with_tools = llm.bind_tools(tools)
    
    for step in range(max_steps):
        print(f"--- 第 {step + 1} 轮推理 ---")
        
        # 调用模型
        response: AIMessage = llm_with_tools.invoke(messages)
        messages.append(response)
        
        # 判断是否有工具调用
        if response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_id = tc["id"]
                
                print(f"  ▶ 调用工具：{tool_name}({tool_args})")
                
                # 执行工具
                tool_func = tool_map.get(tool_name)
                if tool_func:
                    try:
                        result = tool_func.invoke(tool_args)
                        result_str = str(result)
                    except Exception as e:
                        result_str = f"工具执行失败: {e}"
                else:
                    result_str = f"未知工具: {tool_name}"
                
                print(f"  ✔ 工具结果：{result_str}")
                
                # 追加 ToolMessage
                messages.append(ToolMessage(content=result_str, tool_call_id=tool_id))
        else:
            # 最终回答
            print(f"✅ 最终回答：{response.content}")
            return response.content
            
    return "❌ 超过最大推理轮数。"

# 4. 测试
if __name__ == "__main__":
    test_cases = [
        "北京天气怎么样？",
        "帮我算 12 乘以 34",
        "火星天气怎么样？"
    ]
    
    for query in test_cases:
        print("" + "="*60)
        print(f"🤔 用户：{query}")
        react(query)