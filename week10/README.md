# Week 10：全栈 AI 进阶总结

本周已完成全部 7 天的学习挑战：从零手写 ReAct 循环，逐步加入流式输出、人工审核、工具超时降级和 SQLite 对话记忆，最终整合为一个面向生产工程化实践的交互式 CLI Agent。

## 七天成长回顾

| 天数 | 示例 | 完成内容 |
| --- | --- | --- |
| Day 1 | [week10_day1.py](./week10_day1.py) | 使用 OpenAI SDK 手写 ReAct 循环，手动定义工具 JSON Schema，执行工具并回传结果 |
| Day 2 | [week10_day2.py](./week10_day2.py) | 使用 LangChain `@tool`、`bind_tools` 和消息类，掌握工具绑定与手写循环的配合 |
| Day 3 | [week10_day3.py](./week10_day3.py) | 接入 Streaming，边接收边输出文本，并收集流式工具调用信息 |
| Day 4 | [week10_day4.py](./week10_day4.py) | 加入 Human-in-the-loop，执行敏感工具前展示参数并等待人工批准 |
| Day 5 | [week10_day5.py](./week10_day5.py) | 使用线程池与超时结果处理演示工具降级，结合人工审核增强执行流程 |
| Day 6 | [week10_day6.py](./week10_day6.py) | 使用 Python 原生 `sqlite3` 保存、加载对话消息，实现按会话隔离的持久化记忆 |
| Day 7 | [week10_day7.py](./week10_day7.py) | 整合工具调用、流式输出、审核、超时降级与持久化，完成交互式 CLI Agent |

与 Week 9 的 LangGraph Checkpoint 不同，本周重点是亲自管理执行循环、消息协议和数据库读写，理解 Agent 各项能力如何协同工作。

## 核心执行流程

```text
输入会话 ID → 加载 SQLite 历史 → 输入问题并保存
                                  ↓
                        调用模型，流式显示文本
                                  ↓
                        合并响应与 tool_calls
                         ├─ 无工具调用 → 结束本轮
                         └─ 有工具调用 → 查找工具
                                          ↓
                                敏感操作等待人工审核
                                 ├─ 拒绝 → 记录拒绝结果
                                 └─ 批准/普通工具 → 执行与超时处理
                                          ↓
                                保存并回传 ToolMessage
                                          ↓
                                  模型继续下一轮推理
```

模型负责选择工具和生成参数，程序负责实际执行。`tool_call_id` 将工具结果与模型请求关联起来；保存历史时也必须保留这组关系。

Day 7 通过累加流式消息块（`full_response += chunk`）合并文本和工具参数，收集完成后再执行工具。敏感工具使用 `metadata={"is_sensitive": True}` 标记，用户拒绝时也会保存工具结果，让模型知道操作未执行。

## 环境与启动

需要 Python 3.10+ 和可用的 DeepSeek API Key。以下命令从仓库根目录开始：

```powershell
cd week10
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux 对应使用 `python3 -m venv venv` 和 `source venv/bin/activate`。

Day 1 直接使用 `openai` SDK，安装当前 `langchain-openai` 依赖时会一并安装；SQLite 使用 Python 标准库，无需额外安装。本周脚本不依赖 LangGraph 执行图，依赖清单中仍保留了相关包。

在 `week10/.env` 中配置：

```dotenv
DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
```

`MODEL_NAME` 请填写账号可用的模型。Day 2、3、4、6、7 未提供模型名默认值，应显式配置；这些脚本以及 Day 1 使用 `load_dotenv()` 读取环境变量。Day 5 用关键词模拟模型决策，不调用模型 API。

激活环境后，在 `week10` 目录按顺序运行：

```powershell
python week10_day1.py
python week10_day2.py
python week10_day3.py
python week10_day4.py
python week10_day5.py
python week10_day6.py
python week10_day7.py
```

Day 4、5 的邮件示例需要在终端确认；Day 5 输入 `yes` 才批准。Day 6 默认执行固定 `test_session` 的演示，交互入口 `interactive_session()` 在源码中已定义但未启用。Day 7 默认直接进入完整交互模式。

## Day 7：交互式 CLI Agent

启动后输入会话 ID，例如 `week10-demo`；留空会自动生成。再次启动时输入同一个 ID，可以加载该会话已保存的历史。

| 命令 | 功能 |
| --- | --- |
| `help` | 查看命令和工具列表 |
| `new` | 切换到自动生成的新会话，不删除旧会话记录 |
| `exit` | 退出程序 |

可用工具包括模拟天气查询 `get_weather(city)`、整数乘法 `calculator(a, b)`、慢工具 `slow_tool()` 和需人工确认的模拟邮件工具 `send_email(to, subject, body)`。

建议用以下步骤检查各项能力：

1. 输入“北京天气怎么样？再帮我算 12 乘以 34”，观察工具调用、结果回传和流式回答，乘积应为 `408`。
2. 输入“请调用 send_email，给 demo@example.com 发邮件，主题是学习总结，正文是 Week 10 已完成”，在审核提示中输入 `no`，观察拒绝结果；再次请求并输入 `yes`，观察模拟执行结果。
3. 输入“请调用 slow_tool 测试超时降级”，观察超时提示和降级结果。当前实现并不保证 3 秒内返回，原因见下方边界说明。
4. 输入“请记住我叫小明”，退出后重新启动，使用相同会话 ID 问“我叫什么？”，检查持久化记忆。
5. 输入 `new` 后再询问姓名，检查新会话未加载旧会话上下文。

工具是否被选择由模型决定，上述步骤是手动验证路径，不是已执行的测试结果。

## SQLite 持久化设计

Day 6 和 Day 7 都使用相对路径 `agent_memory.db`，数据库生成在启动命令所在目录，建议始终从 `week10` 运行。

- Day 6 使用 `conversation_history` 表；Day 7 使用 `conversations` 表，两者不会自动共享对话记录。
- 按 `session_id` 区分会话，保存 system、human、ai、tool 消息。
- `tool_calls` 以 JSON 保存，工具消息保留 `tool_call_id`，读取时还原为 LangChain 消息对象。
- 同一会话可以跨进程重启继续读取，`new` 仅切换会话 ID。

## 工程化收获与当前边界

本周已把独立能力整合为完整的 CLI 学习项目，覆盖了生产级 Agent 所需的部分工程化基础；正式用于生产前仍需完善以下实现：

- **工具数据**：天气为模拟数据，邮件仅返回字符串，没有真正调用邮件服务。
- **超时控制**：Day 5、7 使用 `future.result(timeout=3)`，但线程池上下文退出时仍会等待正在运行的任务。Day 5 慢工具休眠 5 秒，Day 7 休眠 10 秒，因此超时提示可能在任务结束后才出现，也不会强制取消工具副作用。
- **历史窗口**：Day 6、7 当前通过 `ORDER BY id ASC LIMIT ?` 分别读取最早的 50、200 条消息，并非最近消息。长会话需要按完整工具调用链裁剪或摘要，避免遗漏近期上下文或截断消息配对。
- **异常恢复**：模型网络异常、流中断、消息写入中断后的恢复，以及真正的权限校验和审计仍需补充。
- **循环上限**：Day 7 最多推理 5 轮；达到上限会返回错误文本，但 CLI 当前只补换行，没有显式打印该返回文本。

## 下一步

- 接入真实工具服务，加入请求级超时、取消机制和幂等控制。
- 完善历史窗口、消息事务与失败恢复，补充自动化回归验证。
- 增加结构化日志、调用耗时和费用统计。
- 将 CLI Agent 封装为 FastAPI 接口，再接入前端展示流式回答、审核和会话管理。

返回 [项目总览](../README.md)。
