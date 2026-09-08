# Week 9：从 Function Calling 到可持久化 ReAct Agent

本周围绕 AI Agent 的核心执行链路展开：先观察模型如何生成工具调用请求，再用纯 Python 手写 ReAct 循环，最后把同一套流程迁移到 LangGraph，并通过 SQLite Checkpoint 保存不同会话的对话状态。

## 学习内容

| 天数 | 脚本 | 核心内容 |
| --- | --- | --- |
| Day 1 | `week9_day1.py` | 使用 `@tool` 定义计算、搜索和天气工具，通过 `bind_tools` 观察模型生成的工具名与参数 |
| Day 2 | `week9_day2.py` | 天气工具接入 `wttr.in`，测试一个问题触发一个或多个工具调用的决策能力 |
| Day 3 | `week9_day3.py` | 用纯 Python 实现“模型决策 -> 执行工具 -> 回传结果 -> 再次推理”的 ReAct 闭环 |
| Day 4 | `week9_day4.py` | 使用 `StateGraph`、`ToolNode`、条件边和 `add_messages` 将 ReAct 循环图化 |
| Day 5 | `week9_day5.py` | 使用 `SqliteSaver` 持久化消息状态，并增加模型重试、超时和最大推理次数限制 |

## 从工具调用到 Agent

Function Calling 不会替开发者执行函数。模型只会返回要调用的工具及参数，程序仍需完成工具查找、执行和结果回传。Day 1 和 Day 2 只展示模型的调用决策；从 Day 3 开始，程序才真正闭合整个 Agent 循环。

```text
用户问题
   ↓
模型判断是否需要工具
   ├─ 不需要 → 直接返回最终答案
   └─ 需要   → 生成 tool_calls
                  ↓
              程序执行工具
                  ↓
              ToolMessage 回传结果
                  ↓
              模型继续推理
```

Day 4 用 LangGraph 表达相同过程：`agent` 节点负责调用模型，`tools` 节点负责执行工具，条件边根据最后一条 `AIMessage` 是否包含 `tool_calls` 决定继续循环还是结束。

## 环境要求

- Python 3.10+
- DeepSeek API Key
- Windows PowerShell、macOS 或 Linux
- Day 2 查询实时天气时需要访问 `https://wttr.in`

## 安装依赖

在仓库根目录进入 Week 9：

```powershell
cd week9
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS 或 Linux 使用：

```bash
cd week9
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

当前虚拟环境验证过的主要版本为：

```text
langgraph==1.2.11
langchain-core==1.6.2
langchain-openai==1.6.0
langgraph-checkpoint-sqlite==3.1.1
python-dotenv==1.2.3
requests==2.34.2
```

`requirements.txt` 使用最低版本约束，因此重新安装时可能得到更新版本；依赖升级后应重新执行五个示例。

## 配置模型

在 `week9/.env` 中配置：

```dotenv
DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
```

不要提交包含真实密钥的 `.env` 文件。

目前 Day 1、Day 2、Day 3 读取 `DEEPSEEK_BASE_URL`，Day 4、Day 5 读取 `BASE_URL`，所以示例同时配置两个地址变量。Day 3、Day 4、Day 5 的源码默认模型名与 Day 1、Day 2 不完全一致；显式设置 `MODEL_NAME` 可以保证五个脚本使用同一个可用模型。

也可以只在当前 PowerShell 会话中配置：

```powershell
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:BASE_URL="https://api.deepseek.com"
$env:MODEL_NAME="deepseek-chat"
```

## 运行示例

激活虚拟环境后，在 `week9` 目录逐天运行：

```powershell
python week9_day1.py
python week9_day2.py
python week9_day3.py
python week9_day4.py
python week9_day5.py
```

建议按 Day 1 到 Day 5 的顺序观察输出：

1. Day 1 查看 `tool_calls` 中的工具名称和结构化参数。
2. Day 2 对比单工具与多工具问题的决策结果。天气接口失败时会返回明确标注的模拟降级数据。
3. Day 3 查看每轮 Thought、Action、Observation，以及 `ToolMessage.tool_call_id` 如何关联一次工具调用。
4. Day 4 对比手写循环与 LangGraph 节点、边和状态 Reducer 的对应关系。
5. Day 5 连续执行同一 `thread_id` 和新 `thread_id`，验证会话记忆隔离。

## Day 5 的持久化记忆

Day 5 使用 `SqliteSaver.from_conn_string("checkpoints.db")`，并在上下文管理器内部编译和调用图。运行后会在当前目录生成 `checkpoints.db`。

```python
with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    checkpointer.setup()
    app = workflow.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "session1"}}
    result = app.invoke({"messages": [HumanMessage(content=query)]}, config)
```

同一个 `thread_id` 会继续读取历史状态，不同 `thread_id` 相互隔离。如果需要全新的回归环境，可更换会话 ID；删除数据库会清空全部本地检查点数据。

## 关键实现细节

- `add_messages` 是消息字段的 Reducer。节点只需返回本轮新增消息，LangGraph 会合并到已有历史中。
- `ToolNode` 根据 `AIMessage.tool_calls` 查找并执行已注册工具，并生成对应的 `ToolMessage`。
- `ToolMessage` 必须携带正确的 `tool_call_id`，模型才能把执行结果与之前的工具请求关联起来。
- `temperature=0` 降低演示中的随机性，但不保证模型每次都选择完全相同的工具组合。
- `max_retries=3` 和 `timeout=30` 处理请求层面的短暂失败；`MAX_ITERATIONS=5` 限制 Agent 的推理轮数。这两类保护解决的问题不同。

## 已知边界

- Day 1 的 `search_web`、`get_weather`，Day 2 的 `search_web`，以及 Day 3 到 Day 5 的天气数据包含模拟实现，不能作为生产实时数据使用。
- Day 2 的 `wttr.in` 请求失败、超时或返回非 200 状态时会降级为模拟天气。
- Day 1 和 Day 2 只打印模型返回的工具调用计划，并不执行这些工具。
- Day 3 通过工具名称从 `TOOLS` 字典直接索引，生产代码还应处理未知工具、参数校验失败和工具执行异常。
- `checkpoints.db` 是运行数据，不是源码；共享仓库前应确认它是否需要纳入版本控制。

## 后续实践方向

- 将模拟搜索替换为真实搜索服务，并为外部请求增加重试、限流和缓存。
- 统一五个脚本的环境变量名与默认模型配置。
- 为工具增加 Pydantic 参数模型、权限控制和错误分类。
- 在 LangGraph 中加入人工确认节点、流式输出和可观测性。
- 将 Agent 封装为 FastAPI 服务，再接入前端展示工具执行过程与会话列表。
