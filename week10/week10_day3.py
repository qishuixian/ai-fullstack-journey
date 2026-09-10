import os
import sys
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

load_dotenv()

# 1. 初始化模型（流式模式）
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0,
    streaming=True  # 启用流式
)

# 2. 定义工具
@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气。"""
    weather_db = {"北京": "晴，25度", "上海": "多云，28度", "广州": "雷阵雨，30度"}
    return weather_db.get(city, f"未知城市：{city}")

@tool
def calculator(a: int, b: int) -> int:
    """计算两个整数的乘积。"""
    return a * b

tools = [get_weather, calculator]
tool_map = {tool.name: tool for tool in tools}

# 3. 辅助函数：流式收集并打印
def stream_and_collect(llm_instance, messages):
    """
    流式调用 LLM，实时打印文本，并收集完整的 AIMessage。
    返回 (完整AIMessage, 是否包含tool_calls)
    """
    collected_content = []
    collected_tool_calls = []  # 存储 partial tool calls
    current_tool_call = None   # 当前正在构建的工具调用

    for chunk in llm_instance.stream(messages):
        # 处理文本增量
        if chunk.content:
            collected_content.append(chunk.content)
            print(chunk.content, end="", flush=True)
            time.sleep(0.02)  # 模拟打字速度（可调节）

        # 处理工具调用增量（LangChain 流式会分段给出 tool_call_chunks）
        if hasattr(chunk, 'tool_call_chunks') and chunk.tool_call_chunks:
            for tc_chunk in chunk.tool_call_chunks:
                index = tc_chunk.index
                # 如果是新的工具调用起始
                if len(collected_tool_calls) <= index:
                    collected_tool_calls.append({
                        "name": "",
                        "args": "",
                        "id": tc_chunk.id or ""
                    })
                # 累积 name 和 args
                if tc_chunk.name:
                    collected_tool_calls[index]["name"] += tc_chunk.name
                if tc_chunk.args:
                    collected_tool_calls[index]["args"] += tc_chunk.args
                if tc_chunk.id:
                    collected_tool_calls[index]["id"] = tc_chunk.id

    # 组装最终的 AIMessage
    full_content = "".join(collected_content)
    final_tool_calls = []
    for tc in collected_tool_calls:
        if tc["name"]:  # 只有有 name 才算有效工具调用
            final_tool_calls.append({
                "name": tc["name"],
                "args": tc["args"],  # 仍是 JSON 字符串
                "id": tc["id"]
            })

    # 构造 AIMessage（包含完整 tool_calls 结构）
    ai_msg = AIMessage(content=full_content or None)
    if final_tool_calls:
        # 需要转换为 LangChain 的标准 tool_calls 格式
        from langchain_core.messages.tool import tool_call
        ai_msg.tool_calls = [
            {
                "name": tc["name"],
                "args": json.loads(tc["args"]) if tc["args"] else {},
                "id": tc["id"]
            }
            for tc in final_tool_calls
        ]
    return ai_msg

import json  # 用于解析 args

# 4. ReAct 主循环（流式版）
def react_stream(user_input: str, max_steps: int = 5) -> str:
    messages = [
        SystemMessage(content="你是一个有帮助的助手。你可以使用工具获取信息。"),
        HumanMessage(content=user_input)
    ]

    for step in range(max_steps):
        print(f"\n--- 第 {step + 1} 轮推理 ---")

        # 流式调用并收集完整响应
        ai_msg = stream_and_collect(llm.bind_tools(tools), messages)
        messages.append(ai_msg)

        # 检查是否有工具调用
        if ai_msg.tool_calls:
            for tc in ai_msg.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_id = tc["id"]

                print(f"\n  ▶ 调用工具：{tool_name}({tool_args})")

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

                messages.append(ToolMessage(content=result_str, tool_call_id=tool_id))
        else:
            # 最终答案已在流式过程中打印完毕，这里只需返回
            return ai_msg.content or ""

    return "❌ 超过最大推理轮数。"

# 5. 测试
if __name__ == "__main__":
    test_cases = [
        "北京天气怎么样？",
        "帮我算 12 乘以 34",
        "火星天气怎么样？"
    ]
    for query in test_cases:
        print("\n" + "="*60)
        print(f"🤔 用户：{query}")
        react_stream(query)