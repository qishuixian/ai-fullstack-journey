import json
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

load_dotenv()

# ==================== 1. 数据库初始化 ====================

DB_PATH = "agent_memory.db"

def init_db():
    """创建数据库表（如果不存在）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT,
            tool_calls TEXT,      -- 存储 tool_calls 的 JSON 字符串
            tool_call_id TEXT,    -- 仅 tool 消息使用
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_message(session_id: str, role: str, content: str = None, 
                 tool_calls: list = None, tool_call_id: str = None):
    """保存单条消息到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversation_history (session_id, role, content, tool_calls, tool_call_id, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        role,
        content,
        json.dumps(tool_calls) if tool_calls else None,
        tool_call_id,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def load_history(session_id: str, limit: int = 50) -> list:
    """加载最近的对话历史（最多 limit 条）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, tool_calls, tool_call_id FROM conversation_history
        WHERE session_id = ?
        ORDER BY id ASC
        LIMIT ?
    """, (session_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        role, content, tool_calls_json, tool_call_id = row
        if role == "system":
            messages.append(SystemMessage(content=content))
        elif role == "human":
            messages.append(HumanMessage(content=content))
        elif role == "ai":
            # 如果有 tool_calls，需要还原
            tool_calls = json.loads(tool_calls_json) if tool_calls_json else None
            msg = AIMessage(content=content or "")
            if tool_calls:
                msg.tool_calls = tool_calls
            messages.append(msg)
        elif role == "tool":
            messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
    return messages

# ==================== 2. 工具定义 ====================

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

# ==================== 3. 初始化 LLM ====================

llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0
)

# ==================== 4. ReAct 主循环（带持久化） ====================

def react_persistent(session_id: str, user_input: str, max_steps: int = 5) -> str:
    # 加载历史消息
    messages = load_history(session_id)
    
    # 如果没有历史，添加 system prompt
    if not messages:
        messages.append(SystemMessage(content="你是一个有帮助的助手。你可以使用工具获取信息。"))
        save_message(session_id, "system", content=messages[-1].content)
    
    # 添加用户输入
    messages.append(HumanMessage(content=user_input))
    save_message(session_id, "human", content=user_input)
    
    llm_with_tools = llm.bind_tools(tools)
    
    for step in range(max_steps):
        print(f"\n--- 第 {step + 1} 轮推理 ---")
        
        response: AIMessage = llm_with_tools.invoke(messages)
        messages.append(response)
        
        # 保存 AI 消息（包括 tool_calls）
        save_message(session_id, "ai", 
                     content=response.content,
                     tool_calls=response.tool_calls)
        
        if response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_id = tc["id"]
                
                print(f"  ▶ 调用工具：{tool_name}({tool_args})")
                
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
                
                tool_msg = ToolMessage(content=result_str, tool_call_id=tool_id)
                messages.append(tool_msg)
                save_message(session_id, "tool", 
                             content=result_str, 
                             tool_call_id=tool_id)
        else:
            print(f"✅ 最终回答：{response.content}")
            return response.content
    
    return "❌ 超过最大推理轮数。"

# ==================== 5. 交互式命令行 ====================

def interactive_session():
    """启动交互式会话，支持多轮对话"""
    init_db()
    session_id = input("请输入会话 ID（留空自动生成）: ").strip()
    if not session_id:
        session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"自动生成会话 ID: {session_id}")
    
    print(f"进入会话 {session_id}，输入 'exit' 退出，输入 'new' 开启新会话")
    
    while True:
        user_input = input("\n👤 你: ").strip()
        if user_input.lower() == 'exit':
            break
        elif user_input.lower() == 'new':
            session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            print(f"新会话 ID: {session_id}")
            continue
        
        print(f"🤖 Agent: ", end="")
        answer = react_persistent(session_id, user_input)
        print(answer)

# ==================== 6. 测试 ====================

if __name__ == "__main__":
    # 初始化数据库
    init_db()
    
    # 测试单次对话
    print("="*60)
    print("测试单次对话：")
    react_persistent("test_session", "北京天气怎么样？")
    react_persistent("test_session", "帮我算 12 乘以 34")
    
    # 测试记忆恢复（第二次运行时会加载历史）
    print("\n" + "="*60)
    print("测试记忆恢复（再次询问同一会话）：")
    react_persistent("test_session", "我刚才问了什么？")
    
    # 启动交互式模式（取消注释即可使用）
    # interactive_session()