import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# ==================== 1. 工具函数定义 ====================

def get_weather(city: str) -> str:
    """获取城市天气（模拟正常耗时1秒）"""
    time.sleep(1)
    if city == "火星":
        return "未知城市：火星"
    return f"{city}：晴，25度"

def slow_tool() -> str:
    """模拟一个响应极慢的外部工具（耗时10秒）"""
    print("  [慢工具] 开始执行，预计需要10秒...")
    time.sleep(10)
    return "慢工具执行成功"

def send_email(to: str, subject: str, body: str) -> str:
    """发送邮件（敏感操作）"""
    return f"邮件已发送至 {to}，主题：{subject}"

# ==================== 2. 工具参数模型 ====================

class WeatherInput(BaseModel):
    city: str = Field(..., description="城市名称")

class SlowToolInput(BaseModel):
    pass  # 无参数

class EmailInput(BaseModel):
    to: str = Field(..., description="收件人邮箱")
    subject: str = Field(..., description="邮件主题")
    body: str = Field(..., description="邮件内容")

# ==================== 3. 注册工具 ====================

weather_tool = StructuredTool.from_function(
    func=get_weather,
    name="get_weather",
    description="获取指定城市的天气",
    args_schema=WeatherInput
)

slow_tool_obj = StructuredTool.from_function(
    func=slow_tool,
    name="slow_tool",
    description="一个响应非常慢的测试工具",
    args_schema=SlowToolInput
)

email_tool = StructuredTool.from_function(
    func=send_email,
    name="send_email",
    description="发送邮件",
    args_schema=EmailInput,
    metadata={"is_sensitive": True}  # 标记为敏感工具
)

tools = [weather_tool, slow_tool_obj, email_tool]
tool_map = {tool.name: tool for tool in tools}

# ==================== 4. 人工审核函数 ====================

def human_approve(tool_name: str, tool_args: dict) -> bool:
    print(f"\n⚠️ 需要人工确认的操作：")
    print(f"   工具：{tool_name}")
    print(f"   参数：{json.dumps(tool_args, ensure_ascii=False, indent=2)}")
    while True:
        choice = input("   是否允许执行？(yes/no): ").strip().lower()
        if choice in ["yes", "y"]:
            return True
        elif choice in ["no", "n"]:
            return False
        else:
            print("   请输入 yes 或 no")

# ==================== 5. 带超时降级的工具执行器 ====================

def execute_tool_with_timeout(tool_func, tool_args: dict, timeout: int = 3) -> str:
    """使用线程池执行工具，并设置超时降级"""
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(tool_func.invoke, tool_args)
            result = future.result(timeout=timeout)
            return str(result)
    except FuturesTimeoutError:
        print(f"  ⏰ 工具执行超时（超过 {timeout} 秒），触发降级！")
        return "工具暂时不可用（执行超时），请稍后再试或联系管理员。"
    except Exception as e:
        return f"工具执行失败: {e}"

# ==================== 6. ReAct 主循环 ====================

def react_agent(user_input: str, max_steps: int = 5) -> str:
    messages = [
        SystemMessage(content="你是一个有帮助的助手。你可以使用工具获取信息。"),
        HumanMessage(content=user_input)
    ]

    # 模拟 LLM 响应（测试用，实际应替换为真实 LLM 调用）
    # llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    # llm_with_tools = llm.bind_tools(tools)

    for step in range(max_steps):
        print(f"\n--- 第 {step + 1} 轮推理 ---")

        # 模拟 LLM 返回（测试用）
        response = simulate_llm_response(user_input)
        messages.append(response)

        if response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_id = tc["id"]

                print(f"  ▶ 准备调用工具：{tool_name}({tool_args})")

                # 获取工具对象（安全判空）
                tool_func = tool_map.get(tool_name)
                if tool_func is None:
                    result_str = f"未知工具: {tool_name}"
                    print(f"  ✘ {result_str}")
                    messages.append(ToolMessage(content=result_str, tool_call_id=tool_id))
                    continue

                # 检查是否为敏感工具（安全获取 metadata）
                metadata = getattr(tool_func, "metadata", {})
                is_sensitive = metadata.get("is_sensitive", False)

                if is_sensitive:
                    approved = human_approve(tool_name, tool_args)
                    if not approved:
                        result_str = "用户拒绝了该操作"
                        print(f"  ✘ 用户已拒绝")
                        messages.append(ToolMessage(content=result_str, tool_call_id=tool_id))
                        continue
                    print(f"  ✔ 用户已批准，执行工具...")

                # 执行带超时降级的工具调用
                result_str = execute_tool_with_timeout(tool_func, tool_args, timeout=3)
                print(f"  ✔ 工具结果：{result_str}")
                messages.append(ToolMessage(content=result_str, tool_call_id=tool_id))

        else:
            print(f"✅ 最终回答：{response.content}")
            return response.content

    return "❌ 超过最大推理轮数。"

# ==================== 7. 模拟 LLM 响应（测试用） ====================

class MockResponse:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

def simulate_llm_response(query: str) -> MockResponse:
    """根据查询关键词返回模拟的 LLM 响应"""
    if "天气" in query:
        return MockResponse(tool_calls=[{"name": "get_weather", "args": {"city": "北京"}, "id": "call_1"}])
    elif "慢" in query:
        return MockResponse(tool_calls=[{"name": "slow_tool", "args": {}, "id": "call_2"}])
    elif "邮件" in query:
        return MockResponse(tool_calls=[{"name": "send_email", "args": {"to": "admin@example.com", "subject": "测试", "body": "这是一封测试邮件"}, "id": "call_3"}])
    else:
        return MockResponse(content="我不确定你想做什么，请具体说明。")

# ==================== 8. 测试入口 ====================

if __name__ == "__main__":
    test_cases = [
        "北京天气怎么样？",
        "调用那个很慢的工具",
        "帮我发邮件"
    ]

    for query in test_cases:
        print("\n" + "="*60)
        print(f"🤔 用户：{query}")
        react_agent(query)