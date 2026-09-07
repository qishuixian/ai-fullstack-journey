# Week 8：LangGraph Agent 实践

本目录记录 LangGraph 从基础状态图、工具调用，到多 Agent 协作、持久化记忆和并行执行的练习。

## 学习内容

| 天数 | 脚本 | 内容 |
|------|------|------|
| Day 1 | `week8_day1.py` | StateGraph、共享状态、节点、条件路由与循环 |
| Day 2 | `week8_day2.py` | ReAct Agent、Function Calling、ToolNode 与消息追加 |
| Day 3 | `week8_day3.py` | Supervisor 根据任务路由到计算或搜索 Agent |
| Day 4 | `week8_day4.py` | 自定义工具执行节点、ToolMessage 与循环熔断 |
| Day 5 | `week8_day5.py` | SQLite Checkpoint、会话 ID 与持久化记忆 |
| Day 6 | `week8_day6.py` | 结构化路由、Supervisor + Worker 协作与受控循环 |
| Day 7 | `week8_day7.py` | 使用 `Send` 动态并行分发任务并汇总专家结果 |

## 环境要求

- Python 3.10+
- DeepSeek API Key
- Windows PowerShell

## 安装

在当前目录执行：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 配置模型

项目会自动读取当前目录的 `.env` 文件。创建 `.env` 并填写：

```dotenv
DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
```

也可以只在当前 PowerShell 会话中设置：

```powershell
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:MODEL_NAME="deepseek-chat"
```

## 运行

每一天都可以独立运行，例如：

```powershell
python week8_day1.py
python week8_day5.py
python week8_day6.py
python week8_day7.py
```

Day 7 会把同一个复合问题并行派发给数学专家和搜索专家，再由汇总节点生成最终答案：

```text
用户问题
   └─ Supervisor
      ├─ math_agent   ─┐
      └─ search_agent ─┴─ synthesizer ──> 最终答案
```

## 关键兼容性说明

- 当前依赖版本为 `langgraph==1.2.11`，`Send` 需要从 `langgraph.types` 导入。
- `langchain-openai==1.6.0` 的结构化输出默认使用 `json_schema`。DeepSeek 当前不支持该格式，因此 Day 6 和 Day 7 显式使用 `method="function_calling"`。
- Day 6 和 Day 7 使用 `langchain.agents.create_agent` 执行完整的模型、工具、模型调用流程。
- Day 5、Day 6 和 Day 7 会在当前目录写入 `chat_history.db`。相同 `thread_id` 会复用历史对话；需要全新测试时请更换会话 ID 或使用新的数据库。
- `search_web` 返回的是本地模拟天气数据，用于演示工具调用，并非实时天气查询。

## 依赖版本

主要依赖见 `requirements.txt`：

```text
langchain==1.3.18
langchain-openai==1.6.0
langgraph==1.2.11
langgraph-prebuilt==1.1.0
```
