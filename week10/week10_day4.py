import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

load_dotenv()

# 1. 初始化模型
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0
)

# 2. 定义工具（含敏感标记）
@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气。"""
    weather_db = {"北京": "晴，25度", "上海": "多云，28度", "广州": "雷阵雨，30度"}
    return weather_db.get(city, f"未知城市：{city}")

@tool
def calculator(a: int, b: int) -> int:
    """计算两个整数的乘积。"""
    return a * b

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """发送一封电子邮件（敏感操作，需要人工确认）。"""
    # 模拟发送
    return f"邮件已发送至 {to}，主题：{subject}"

tools = [get_weather, calculator, send_email]
tool_map = {tool.name: tool for tool in tools}

# 3. 人工审核函数
def human_approve(tool_name: str, tool_args: dict) -> bool:
    """
    暂停执行，等待用户输入 yes/no。
    返回 True 表示同意，False 表示拒绝。
    """
    print(f"\n⚠️ 需要人工确认的操作：")
    print(f"   工具：{tool_name}")
    print(f"   参数：{json.dumps(tool_args, ensure_ascii=False, indent=2)}")
    while True:
        user_input = input("   是否允许执行？(yes/no): ").strip().lower()
        if user_input in ("yes", "y"):
            return True
        elif user_input in ("no", "n"):
            return False
        else:
            print("   请输入 yes 或 no")

# 4. ReAct 主循环（含人工审核）
def react_with_hitl(user_input: str, max_steps: int = 5) -> str:
    messages = [
        SystemMessage(content="你是一个有帮助的助手。你可以使用工具获取信息。"),
        HumanMessage(content=user_input)
    ]
    
    llm_with_tools = llm.bind_tools(tools)
    
    for step in range(max_steps):
        print(f"\n--- 第 {step + 1} 轮推理 ---")
        
        response: AIMessage = llm_with_tools.invoke(messages)
        messages.append(response)
        
        if response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_id = tc["id"]
                
                print(f"  ▶ 准备调用工具：{tool_name}({tool_args})")
                
                # 获取工具对象
                tool_func = tool_map.get(tool_name)
                
                # 【修复点】：通过工具名称（或 metadata）判断是否敏感
                is_sensitive = tool_name == "send_email" 
                # 进阶写法：如果创建工具时传了 metadata={"is_sensitive": True}，可以用下面这行：
                # is_sensitive = tool_func and tool_func.metadata.get("is_sensitive", False)
                
                if tool_func and is_sensitive:
                    # 需要人工审核
                    approved = human_approve(tool_name, tool_args)
                    if approved:
                        print("  ✔ 用户已批准，执行工具...")
                        try:
                            result = tool_func.invoke(tool_args)
                            result_str = str(result)
                        except Exception as e:
                            result_str = f"工具执行失败: {e}"
                    else:
                        print("  ✘ 用户已拒绝")
                        result_str = "用户拒绝了该操作"
                else:
                    # 非敏感工具，直接执行
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
            print(f"✅ 最终回答：{response.content}")
            return response.content
    
    return "❌ 超过最大推理轮数。"
# 5. 测试
if __name__ == "__main__":
    test_cases = [
        "北京天气怎么样？",
        "帮我算 12 乘以 34",
        "帮我发一封邮件给 admin@example.com，主题为'测试'，内容为'这是一封测试邮件'"
    ]
    
    for query in test_cases:
        print("\n" + "="*60)
        print(f"🤔 用户：{query}")
        react_with_hitl(query)