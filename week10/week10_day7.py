#!/usr/bin/env python3
"""
Week 10 Day 7 - 综合 CLI Agent
整合：工具调用、超时降级、人工审核、流式输出、SQLite 持久化
"""

import json
import os
import sys
import time
import sqlite3
import concurrent.futures
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool

load_dotenv()

# ==================== 配置 ====================
DB_PATH = "agent_memory.db"
TIMEOUT_SECONDS = 3       # 工具超时时间
MAX_STEPS = 5             # 最大推理轮数
STREAM_DELAY = 0.03       # 流式输出字符间隔（秒）

# ==================== 1. 工具定义 ====================

def get_weather(city: str) -> str:
    """查询指定城市的天气。"""
    weather_db = {"北京": "晴，25度", "上海": "多云，28度", "广州": "雷阵雨，30度"}
    time.sleep(0.5)  # 模拟正常延迟
    return weather_db.get(city, f"未知城市：{city}")

def calculator(a: int, b: int) -> int:
    """计算两个整数的乘积。"""
    return a * b

def slow_tool() -> str:
    """模拟一个响应极慢的外部工具。"""
    print("  [慢工具] 开始执行，预计需要10秒...")
    time.sleep(10)
    return "慢工具执行成功"

def send_email(to: str, subject: str, body: str) -> str:
    """发送一封电子邮件（敏感操作，需要人工确认）。"""
    return f"邮件已发送至 {to}，主题：{subject}"

# 注册工具
weather_tool = StructuredTool.from_function(func=get_weather, name="get_weather")
calc_tool = StructuredTool.from_function(func=calculator, name="calculator")
slow_tool_obj = StructuredTool.from_function(func=slow_tool, name="slow_tool")
email_tool = StructuredTool.from_function(
    func=send_email,
    name="send_email",
    metadata={"is_sensitive": True}  # 标记敏感
)

tools = [weather_tool, calc_tool, slow_tool_obj, email_tool]
tool_map = {t.name: t for t in tools}

# ==================== 2. 数据库操作 ====================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT,
            tool_calls TEXT,
            tool_call_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_message(session_id: str, role: str, content: str = None,
                 tool_calls: list = None, tool_call_id: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO conversations (session_id, role, content, tool_calls, tool_call_id)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, role, content,
          json.dumps(tool_calls) if tool_calls else None,
          tool_call_id))
    conn.commit()
    conn.close()

def load_history(session_id: str, limit: int = 100) -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT role, content, tool_calls, tool_call_id
        FROM conversations
        WHERE session_id = ?
        ORDER BY id ASC
        LIMIT ?
    """, (session_id, limit))
    rows = c.fetchall()
    conn.close()

    messages = []
    for role, content, tc_json, tc_id in rows:
        if role == "system":
            messages.append(SystemMessage(content=content))
        elif role == "human":
            messages.append(HumanMessage(content=content))
        elif role == "ai":
            tool_calls = json.loads(tc_json) if tc_json else None
            msg = AIMessage(content=content or "")
            if tool_calls:
                msg.tool_calls = tool_calls
            messages.append(msg)
        elif role == "tool":
            messages.append(ToolMessage(content=content, tool_call_id=tc_id))
    return messages

# ==================== 3. 工具执行器（超时降级） ====================

def execute_tool_with_timeout(tool_func, tool_args: dict, timeout: int = TIMEOUT_SECONDS) -> str:
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(tool_func.invoke, tool_args)
            return str(future.result(timeout=timeout))
    except concurrent.futures.TimeoutError:
        print(f"  ⏰ 工具执行超时（超过 {timeout} 秒），触发降级！")
        return "工具暂时不可用（执行超时），请稍后再试或联系管理员。"
    except Exception as e:
        return f"工具执行失败: {e}"

# ==================== 4. 人工审核 ====================

def human_approve(tool_name: str, tool_args: dict) -> bool:
    print(f"\n⚠️ 需要人工确认的操作：")
    print(f"   工具：{tool_name}")
    print(f"   参数：{json.dumps(tool_args, ensure_ascii=False, indent=2)}")
    while True:
        choice = input("   是否允许执行？(yes/no): ").strip().lower()
        if choice in ("yes", "y"):
            return True
        elif choice in ("no", "n"):
            return False
        print("   请输入 yes 或 no")

# ==================== 5. 流式输出辅助 ====================

def stream_text(text: str, delay: float = STREAM_DELAY):
    """逐字打印文本，模拟打字效果"""
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()  # 换行

# ==================== 6. LLM 初始化 ====================

llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0,
    streaming=True  # 启用流式
)

# ==================== 7. ReAct 主循环（整合版） ====================

def react_agent(session_id: str, user_input: str) -> str:
    # 加载历史
    messages = load_history(session_id)
    if not messages:
        messages.append(SystemMessage(content="你是一个有帮助的助手。你可以使用工具获取信息。"))
        save_message(session_id, "system", content=messages[-1].content)

    # 添加用户输入
    messages.append(HumanMessage(content=user_input))
    save_message(session_id, "human", content=user_input)

    llm_with_tools = llm.bind_tools(tools)

    for step in range(MAX_STEPS):
        print(f"\n--- 第 {step+1} 轮推理 ---")

        # 流式收集完整响应
        collected_content = []
        collected_tool_calls = []

        for chunk in llm_with_tools.stream(messages):
            if chunk.content:
                collected_content.append(chunk.content)
                print(chunk.content, end="", flush=True)
                time.sleep(STREAM_DELAY)

            if chunk.tool_call_chunks:
                for tc_chunk in chunk.tool_call_chunks:
                    idx = tc_chunk.index if hasattr(tc_chunk, 'index') else 0
                    while len(collected_tool_calls) <= idx:
                        collected_tool_calls.append({"name": "", "args": "", "id": ""})
                    if tc_chunk.name:
                        collected_tool_calls[idx]["name"] += tc_chunk.name
                    if tc_chunk.args:
                        collected_tool_calls[idx]["args"] += tc_chunk.args
                    if tc_chunk.id:
                        collected_tool_calls[idx]["id"] = tc_chunk.id

        full_content = "".join(collected_content)
        final_tool_calls = []
        for tc in collected_tool_calls:
            if tc["name"]:
                final_tool_calls.append({
                    "name": tc["name"],
                    "args": json.loads(tc["args"]) if tc["args"] else {},
                    "id": tc["id"]
                })

        # 构造 AIMessage
        ai_msg = AIMessage(content=full_content or "")
        if final_tool_calls:
            ai_msg.tool_calls = final_tool_calls

        messages.append(ai_msg)
        save_message(session_id, "ai", content=full_content, tool_calls=final_tool_calls)

        # 处理工具调用
        if final_tool_calls:
            for tc in final_tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_id = tc["id"]

                print(f"\n  ▶ 准备调用工具：{tool_name}({tool_args})")

                tool_func = tool_map.get(tool_name)
                if tool_func is None:
                    result_str = f"未知工具: {tool_name}"
                    print(f"  ✘ {result_str}")
                else:
                    # 检查敏感工具
                    metadata = getattr(tool_func, "metadata", {})
                    if not isinstance(metadata, dict):
                        metadata = {}
                    if metadata.get("is_sensitive", False):
                        if not human_approve(tool_name, tool_args):
                            result_str = "用户拒绝了该操作"
                            print(f"  ✘ 用户已拒绝")
                            tool_msg = ToolMessage(content=result_str, tool_call_id=tool_id)
                            messages.append(tool_msg)
                            save_message(session_id, "tool", content=result_str, tool_call_id=tool_id)
                            continue
                        print(f"  ✔ 用户已批准，执行工具...")

                    result_str = execute_tool_with_timeout(tool_func, tool_args)
                    print(f"  ✔ 工具结果：{result_str}")

                tool_msg = ToolMessage(content=result_str, tool_call_id=tool_id)
                messages.append(tool_msg)
                save_message(session_id, "tool", content=result_str, tool_call_id=tool_id)
        else:
            # 最终回答已流式输出，直接返回
            return full_content

    return "❌ 超过最大推理轮数。"

# ==================== 8. 交互式 CLI ====================

def interactive_cli():
    """主交互循环"""
    init_db()
    print("=" * 55)
    print("  🧠 AI Agent CLI - Week 10 综合版")
    print("  输入 'exit' 退出 | 'new' 新建会话 | 'help' 查看帮助")
    print("=" * 55)

    session_id = input("请输入会话 ID（留空自动生成）: ").strip()
    if not session_id:
        session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"自动生成会话 ID: {session_id}")

    while True:
        try:
            user_input = input("\n👤 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("👋 再见！")
            break
        elif user_input.lower() == "new":
            session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            print(f"🆕 新会话 ID: {session_id}")
            continue
        elif user_input.lower() == "help":
            print("""
可用命令：
  exit  - 退出程序
  new   - 开启新会话（清空上下文）
  help  - 显示此帮助

支持的工具：
  - get_weather(city)   : 查询天气
  - calculator(a, b)    : 计算乘积
  - slow_tool()         : 模拟慢工具（测试超时降级）
  - send_email(...)     : 发送邮件（敏感，需人工审核）
            """)
            continue

        print("🤖 Agent: ", end="", flush=True)
        answer = react_agent(session_id, user_input)
        if answer:
            print()  # 流式输出已打印内容，这里只是换行

# ==================== 9. 入口 ====================

if __name__ == "__main__":
    interactive_cli()