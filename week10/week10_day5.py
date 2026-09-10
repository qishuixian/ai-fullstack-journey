import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# --- 1. 模拟工具函数 ---
def get_weather(city: str) -> str:
    """获取城市天气"""
    # 模拟正常耗时
    import time
    time.sleep(1) 
    if city == "火星":
        return "未知城市：火星"
    return f"{city}：晴，25度"

def slow_tool() -> str:
    """模拟一个响应极慢的外部工具"""
    import time
    print("  [慢工具] 开始执行，预计需要10秒...")
    time.sleep(10)
    return "慢工具执行成功"

def send_email(to: str, subject: str, body: str) -> str:
    """发送邮件（敏感工具）"""
    return f"邮件已发送至 {to}，主题：{subject}"

# --- 2. 工具参数模型 ---
class WeatherInput(BaseModel):
    city: str = Field(..., description="城市名称")

class EmailInput(BaseModel):
    to: str = Field(..., description="收件人邮箱")
    subject: str = Field(..., description="邮件主题")
    body: str = Field(..., description="邮件内容")

# --- 3. 注册工具 ---
tools = [
    StructuredTool.from_function(
        func=get_weather,
        name="get_weather",
        description="获取指定城市的天气",
        args_schema=WeatherInput
    ),
    StructuredTool.from_function(
        func=slow_tool,
        name="slow_tool",
        description="一个响应非常慢的测试工具"
    ),
    StructuredTool.from_function(
        func=send_email,
        name="send_email",
        description="发送邮件",
        args_schema=EmailInput,
        metadata={"is_sensitive": True}
    )
]

tool_map = {t.name: t for t in tools}

# --- 4. 人工审核函数 ---
def human_approve(tool_name: str, tool_args: dict) -> bool:
    print(f"需要人工确认的操作：")
    print(f"工具：{tool_name}")
    print(f"参数：{json.dumps(tool_args, ensure_ascii=False, indent=2)}")
    while True:
        choice = input("是否允许执行？(yes/no): ").strip().lower()
        if choice in ["yes", "y"]:
            return True
        elif choice in ["no", "n"]:
            return False
        else:
            print("请输入 yes 或 no")

# --- 5. 带超时和降级的工具执行器 ---
def execute_tool_with_timeout(tool_func, tool_args: dict, timeout: int = 3) -> str:
    """使用线程池执行工具，并设置超时降级"""
    try:
        # 使用线程池提交任务
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(tool_func.invoke, tool_args)
            # 等待结果，设置超时时间
            result = future.result(timeout=timeout)
            return str(result)
    except FuturesTimeoutError:
        # 捕获超时异常，返回降级消息
        print(f"  ⏰ 工具执行超时（超过 {timeout} 秒），触发降级！")
        return "工具暂时不可用（执行超时），请稍后再试或联系管理员。"
    except Exception as e:
        return f"工具执行失败: {e}"

# --- 6. ReAct 主循环 ---
def react_agent(user_input: str, max_steps: int = 5) -> str:
    messages = [
        SystemMessage(content="你是一个有帮助的助手。你可以使用工具获取信息。"),
        HumanMessage(content=user_input)
    ]
    
    # 初始化 LLM 和绑定工具（请根据实际环境替换 llm 对象）
    # llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    # llm_with_tools = llm.bind_tools(tools)
    
    for step in range(max_steps):
        print(f"--- 第 {step + 1} 轮推理 ---")
        
        # response: AIMessage = llm_with_tools.invoke(messages)
        # 模拟 LLM 响应（测试用）
        response = simulate_llm_response(user_input)
        messages.append(response)
        
        if response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_id = tc["id"]
                
                print(f"  ▶ 准备调用工具：{tool_name}({tool_args})")
                
                tool_func = tool_map.get(tool_name)
                if not tool_func:
                    result_str = f"未知工具: {tool_name}"
                else:
                    # 检查敏感工具
                    is_sensitive = tool_func.metadata.get("is_sensitive", False)
                    if is_sensitive:
                        approved = human_approve(tool_name, tool_args)
                        if not approved:
                            result_str = "用户拒绝了该操作"
                            print(f"  ✘ 用户已拒绝")
                            messages.append(ToolMessage(content=result_str, tool_call_id=tool_id))
                            continue
                        print(f"  ✔ 用户已批准，执行工具...")
                    
                    # 【核心】调用带超时降级的方法（超时时间设为 3 秒）
                    result_str = execute_tool_with_timeout(tool_func, tool_args, timeout=3)
                    print(f"  ✔ 工具结果：{result_str}")
                
                messages.append(ToolMessage(content=result_str, tool_call_id=tool_id))
        else:
            print(f"✅ 最终回答：{response.content}")
            return response.content
            
    return "❌ 超过最大推理轮数。"

# --- 模拟 LLM 响应（用于本地测试，实际使用时请删除并启用真实 LLM） ---
class MockResponse:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

def simulate_llm_response(query: str) -> MockResponse:
    if "天气" in query:
        return MockResponse(tool_calls=[{"name": "get_weather", "args": {"city": "北京"}, "id": "1"}])
    elif "慢" in query:
        return MockResponse(tool_calls=[{"name": "slow_tool", "args": {}, "id": "2"}])
    elif "邮件" in query:
        return MockResponse(tool_calls=[{"name": "send_email", "args": {"to": "a@b.com", "subject": "t", "body": "b"}, "id": "3"}])
    else:
        return MockResponse(content="处理完成。")

# --- 7. 测试 ---
if __name__ == "__main__":
    test_cases = [
        "北京天气怎么样？",
        "调用那个很慢的工具",
        "帮我发邮件"
    ]
    
    for query in test_cases:
        print("" + "="*60)
        print(f"🤔 用户：{query}")
        react_agent(query)