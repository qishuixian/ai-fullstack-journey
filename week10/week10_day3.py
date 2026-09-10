import os
import sys
import time
import json  # 用于解析 args
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
def stream_and_collect(llm_with_tools, messages):
    full_content = ""
    final_tool_calls = []
    
    for chunk in llm_with_tools.stream(messages):
        if chunk.content:
            print(chunk.content, end="", flush=True)
            full_content += chunk.content
            
        if chunk.tool_call_chunks:
            for tc_chunk in chunk.tool_call_chunks:
                # 兼容处理：LangChain 流式输出时，tc_chunk 可能是字典或对象
                tc_index = tc_chunk.get("index") if isinstance(tc_chunk, dict) else tc_chunk.index
                tc_id = tc_chunk.get("id") if isinstance(tc_chunk, dict) else tc_chunk.id
                tc_name = tc_chunk.get("name") if isinstance(tc_chunk, dict) else tc_chunk.name
                tc_args = tc_chunk.get("args") if isinstance(tc_chunk, dict) else tc_chunk.args
                
                # 兼容 DeepSeek/OpenAI 流式缺失 index 的情况
                if tc_index is None:
                    tc_index = 0 
                
                # 找是否已经存在该工具调用
                existing = None
                for ftc in final_tool_calls:
                    if ftc["id"] == tc_id or (tc_id is None and ftc["index"] == tc_index):
                        existing = ftc
                        break
                        
                if existing:
                    if tc_name: existing["name"] = tc_name
                    if tc_args: existing["args"] += tc_args
                    if tc_id: existing["id"] = tc_id
                else:
                    final_tool_calls.append({
                        "name": tc_name,
                        "args": tc_args or "",
                        "id": tc_id,
                        "index": tc_index
                    })

    # 构造 AIMessage
    ai_msg = AIMessage(content=full_content or "")  # 修复点：确保 content 永远是字符串，不能是 None
    
    if final_tool_calls:
        ai_msg.tool_calls = [
            {
                "name": tc["name"],
                "args": json.loads(tc["args"]) if tc["args"] else {},
                "id": tc["id"]
            }
            for tc in final_tool_calls
        ]
    return ai_msg

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