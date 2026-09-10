import time
import concurrent.futures
from langchain_core.tools import StructuredTool
# 【修复】ToolMessage 正确导入路径是在 langchain_core.messages 下
from langchain_core.messages import ToolMessage

# ==================== 1. 定义工具 ====================

def get_weather(city: str) -> str:
    """获取指定城市的天气"""
    return f"{city}：晴，25度"

def send_email_func(to: str, subject: str, body: str) -> str:
    """发送邮件"""
    return f"邮件已发送至 {to}，主题：{subject}"

def slow_tool() -> str:
    """一个很慢的工具"""
    time.sleep(5)
    return "慢工具执行完毕"

# 注册工具（显式指定 name 以防默认名称不匹配）
weather_tool = StructuredTool.from_function(func=get_weather, name="get_weather")
email_tool = StructuredTool.from_function(
    func=send_email_func, 
    name="send_email",
    metadata={"is_sensitive": True}  # 标记敏感工具
)
slow_tool_obj = StructuredTool.from_function(func=slow_tool, name="slow_tool")

tools = [weather_tool, email_tool, slow_tool_obj]
tool_map = {tool.name: tool for tool in tools}

# ==================== 2. 人工审核 ====================

def human_approve(tool_name: str, tool_args: dict) -> bool:
    print(f"  ⚠️ 需要人工确认的操作：{tool_name}")
    print(f"  参数：{tool_args}")
    choice = input("  是否允许执行？(yes/no): ").strip().lower()
    return choice == "yes"

# ==================== 3. 超时降级 ====================

def execute_tool_with_timeout(tool_func, tool_args: dict, timeout: int = 3) -> str:
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(tool_func.invoke, tool_args)
            return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        return f"工具执行超时（超过 {timeout} 秒），已降级处理"

# ==================== 4. Agent 主循环 ====================

def react_agent(user_input: str):
    print(f"{'='*60}")
    print(f"🤔 用户：{user_input}")

    # 模拟 LLM 响应
    if "天气" in user_input:
        tool_calls = [{"name": "get_weather", "args": {"city": "北京"}, "id": "1"}]
    elif "慢" in user_input:
        tool_calls = [{"name": "slow_tool", "args": {}, "id": "2"}]
    elif "邮件" in user_input:
        tool_calls = [{"name": "send_email", "args": {"to": "admin@example.com", "subject": "测试", "body": "这是一封测试邮件"}, "id": "3"}]
    else:
        print("✅ 最终回答：处理完成。")
        return

    print("--- 第 1 轮推理 ---")

    for tc in tool_calls:
        tool_name = tc["name"]
        tool_args = tc["args"]
        tool_id = tc["id"]

        print(f"  ▶ 准备调用工具：{tool_name}({tool_args})")

        # 1. 获取工具（防工具不存在）
        tool_func = tool_map.get(tool_name)
        if tool_func is None:
            print(f"  ✘ 未知工具：{tool_name}")
            continue

        # 2. 安全获取 metadata（防 metadata 为 None 导致崩溃）
        metadata = getattr(tool_func, "metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        # 3. 检查敏感工具
        if metadata.get("is_sensitive", False):
            if not human_approve(tool_name, tool_args):
                print("  ✘ 用户已拒绝")
                continue
            print("  ✔ 用户已批准，执行工具...")

        # 4. 执行工具（带超时）
        result = execute_tool_with_timeout(tool_func, tool_args, timeout=3)
        print(f"  ✔ 工具结果：{result}")
        
        # 构造 ToolMessage（演示用）
        messages = [ToolMessage(content=result, tool_call_id=tool_id)]
        print(f"  📨 生成消息：{messages[0]}")

    print("✅ 最终回答：操作完成。")

# ==================== 5. 运行测试 ====================

if __name__ == "__main__":
    react_agent("北京天气怎么样？")
    react_agent("调用那个很慢的工具")
    react_agent("帮我发邮件")