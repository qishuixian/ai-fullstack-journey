# Week 11 · ReAct Studio

把 Week 10 Day 7 的 CLI Agent 搬上浏览器：输入任务后，实时查看模型公开回复、推理轮次、工具参数和执行结果；敏感操作在浏览器审核后继续执行。

参考 [Week 7 项目](../week7/langchain-project/README.md) 的 FastAPI + Vue 结构，使用 Vue 3、TypeScript、Vite、Element Plus。本周保留 [Week 10 Day 7](../week10/week10_day7.py) 的手写 ReAct 循环，不替换成 `create_agent`。不展示模型内部隐藏思维链。

学习路线：Week 9 建立 LangGraph 的图思维 → Week 10 手写 ReAct 理解执行原理 → Week 11 将 Agent 改造成可交互的 Web 应用。Day 1–7 的功能整合在同一套前后端中，按下表定位学习入口即可。

## 访问方式

| 模式 | 页面地址 | 需要启动的服务 |
| --- | --- | --- |
| 前后端开发 | <http://localhost:8003> | Vite 8003 + FastAPI 8083 |
| 打包后运行 | <http://127.0.0.1:8083> | 先构建前端，再启动 FastAPI 8083 |
| API 文档 | <http://127.0.0.1:8083/docs> | FastAPI 8083 |

本周端口固定为**后端 8083、前端 8003**。建议始终使用同一个页面地址：`localhost`、`127.0.0.1` 和不同端口拥有独立的 localStorage，因此不会共用浏览器里的会话列表。

## 目录与七天产出

```text
week11/
├── backend/
│   ├── main.py          # FastAPI、SSE、审核协调、静态文件托管
│   ├── agent.py         # 异步生成器 react_agent、四种工具
│   ├── store.py         # SQLite，会话隔离与原子提交
│   ├── test_app.py      # 无 API 费用的协议与 Agent 回归测试
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/App.vue      # EventSource、打字机、审核弹窗、会话列表
    ├── src/style.css
    └── vite.config.ts   # 8003 → 8083 代理、构建到 backend/static
```

| 天数 | 实现 | 回归入口 |
| --- | --- | --- |
| Day 1 | 异步 ReAct + StreamingResponse | `/chat` 返回 text/event-stream |
| Day 2 | Vue3 + 原生 EventSource | 首页发送问题，收到回复 |
| Day 3 | setInterval 打字机、气泡动画、工具卡片 | 天气与乘法示例 |
| Day 4 | el-dialog + POST /approve | 模拟邮件，批准或拒绝 |
| Day 5 | localStorage 会话列表 + SQLite 历史 | 新建、切换、刷新 |
| Day 6 | 编号轮次、连线、工具结果状态 | 多工具任务 |
| Day 7 | CORS、开发代理、单端口静态部署 | 构建后访问 8083 |

## 本地启动（Windows PowerShell）

要求 Python 3.10+、Node.js 20.19+ 或 22.12+。旧版 Node 14 无法运行本项目。

终端一，从仓库根目录运行：

```powershell
cd week11/backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# 编辑 .env：填写你自己的 DEEPSEEK_API_KEY
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8083 --reload
```

已有 `.env` 时跳过复制，避免覆盖自己的配置。配置项沿用 Week 7：`load_dotenv`、`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`（默认 `https://api.deepseek.com`）、`MODEL_NAME`（默认 `deepseek-chat`）。模型延迟初始化，没配置密钥也能启动服务和运行测试。

终端二，从仓库根目录运行：

```powershell
cd week11/frontend
npm install
npm run dev
```

- 前端：<http://localhost:8003>
- 后端与接口文档：<http://127.0.0.1:8083/docs>
- 健康检查：<http://127.0.0.1:8083/health>

前端使用同源相对地址，Vite 将 `/chat`、`/approve`、`/sessions`、`/health` 转发至 8083。后端 CORS 仅放行本地 8003 的两个来源。

### 环境变量

在 `backend/.env` 中配置，修改后重启后端。不要将真实密钥提交到 Git。

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 无 | 调用真实模型必填 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | OpenAI 兼容接口地址 |
| `MODEL_NAME` | `deepseek-chat` | 模型名称 |
| `TOOL_TIMEOUT_SECONDS` | `3` | 单次工具执行超时秒数 |
| `APPROVAL_TIMEOUT_SECONDS` | `120` | 等待人工审核的超时秒数 |
| `AGENT_DB_PATH` | `backend/agent_memory.db` 的绝对路径 | SQLite 文件位置，建议自定义时也使用绝对路径 |

`/health` 返回的 `model_configured: true` 只表示已读取到非空密钥，不代表密钥有效或模型服务可达；发送一次任务才能验证真实调用。

## 从 CLI 到异步事件

`agent.py` 改编自 `../week10/week10_day7.py` 的 `react_agent`：仍然是加载历史 → 用户消息 → 最多五轮模型调用 → 合并 chunk → AIMessage → 工具 → ToolMessage → 下一轮。使用 `model.astream()` 和 `full_response += chunk` 合并工具参数分片；每有可展示的信息便 `yield` 事件，服务端将它编码成 `data: JSON\n\n`。

CLI 的 `input()` 审核改成 Future：生成独立 `approval_id`，前端 POST 决定后唤醒 Agent。默认等待 120 秒，超时拒绝，断线清理等待项。工具改为可取消的异步调用，`asyncio.wait_for` 默认 3 秒超时，避免旧版线程池退出仍等待慢任务的问题。

```mermaid
sequenceDiagram
    participant UI as Vue 浏览器
    participant API as FastAPI
    participant Agent as react_agent
    participant Model as DeepSeek
    UI->>API: GET /chat（session_id、request_id、message）
    API->>Agent: 启动异步生成器
    Agent->>Model: astream(messages)
    Model-->>Agent: 文本或工具调用分片
    Agent-->>API: yield step / token / tool_call
    API-->>UI: SSE data 事件
    opt 敏感工具
        Agent-->>UI: approval_required（经 SSE）
        UI->>API: POST /approve
        API-->>Agent: Future 返回批准或拒绝
    end
    Agent-->>UI: tool_result（经 SSE）
    Agent->>Model: 携带 ToolMessage 继续下一轮
    Model-->>UI: 最终公开回复（经 SSE）
    API->>API: 原子保存完整轮次
    API-->>UI: done，关闭连接
```

| 接口 | 请求 | 返回 |
| --- | --- | --- |
| POST `/sessions` | `{}` | `{id, title}` |
| GET `/sessions/{id}` | URL 中的会话 ID | `{id, title, turns}` |
| GET `/chat` | `session_id`、`request_id`、`message`（1–2000 字符） | SSE |
| POST `/approve` | `{session_id, approval_id, approved: true/false}` | `{ok: true}` |
| GET `/health` | 无 | 服务状态和是否配置密钥 |

SSE 事件：`step`（轮次）、`token`（公开文本分片）、`tool_call`（工具和参数）、`approval_required`、`approval_result`、`tool_result`、`done`、`error`。无数据时每 15 秒发送注释心跳。前端收到终止或网络错误主动 `EventSource.close()`，避免浏览器自动重连导致重复执行；后端也拒绝已完成的 `request_id`。

同一会话同一时间仅允许一次运行（409），不同会话互不阻塞。界面生成时暂不允许切换或新建，可先停止。完整轮次的模型消息与展示事件在同一 SQLite 事务里保存；异常或取消时不保存半轮上下文。停止发生在完成边界时，服务端可能已保存，重新载入会话即可核对。页面刷新后从后端恢复已完成轮次。

### 前端展示与状态恢复

- `App.vue` 使用浏览器原生 `EventSource` 订阅事件，审核决定通过 `fetch` POST 提交。
- 文本进入缓冲队列，由 `setInterval` 每 20 毫秒显示最多 3 个 Unicode 字符，形成打字机效果；收到 `done` 后仍会显示完剩余文本。
- 工具卡片展示名称、完整参数和执行结果；推理步骤展示轮次编号，审核结果保留在轨迹中。
- 后端保存原始 SSE 展示事件；前端读取历史时合并同一轮连续文本分片，避免刷新后每个分片变成独立段落。
- Element Plus 按需引入按钮、弹窗及消息组件样式，页面布局和动画使用 `style.css`。

## 工具与人工审核

- `get_weather(city)`：北京、上海、广州的固定模拟天气，不联网查询。
- `calculator(a, b)`：两个整数相乘。
- `slow_tool()`：模拟十秒耗时，用于验证三秒超时与降级。
- `send_email(to, subject, body)`：敏感工具，必须审核；仅返回模拟结果，不会发送真实邮件。

审核使用随机 ID 并验证所属会话，重复、过期或跨会话审核返回 409。每一次敏感工具调用都单独审核。拒绝或超时结果作为 ToolMessage 交回模型，模型仍可继续解释结果。

## 回归测试

```powershell
cd week11/backend
.\venv\Scripts\python.exe -m unittest -v test_app
cd ../frontend
npm run build
```

自动测试使用分片假模型驱动真实 ReAct 循环，不调用 DeepSeek。覆盖工具分片合并、SSE 结束、持久化、会话隔离、请求去重、并发拒绝、批准/拒绝、跨会话及重复审核、工具与审核超时、异常回滚、取消清理。

### 已完成的验证（2026-09-10）

| 验证项 | 结果与范围 |
| --- | --- |
| 后端自动测试 | 6 项测试通过；审核测试同时覆盖批准和拒绝两个分支 |
| 前端编译 | `vue-tsc --noEmit` 与 Vite 生产构建通过 |
| 开发代理与 CORS | 通过 8003 访问 `/health` 返回 200；本地 8003 来源的预检请求返回正确的允许来源 |
| 单端口页面 | 8083 成功提供打包后的页面和静态资源 |
| 浏览器审核联调 | 临时测试模型触发审核弹窗，批准后显示模拟工具结果与完成回复 |
| 历史恢复 | 浏览器刷新后恢复完整执行轨迹；文本分片合并后连续显示 |
| 真实模型调用 | 请求“请调用 calculator 计算12乘8，然后简短回答。”，工具返回 `96`，SSE 最后收到 `done` |

以上为实现时的验证记录，不代表每次启动都会自动执行。真实模型验证覆盖计算器链路；邮件审核的浏览器验证使用测试模型，未发送真实邮件。

真实模型人工回归（需有效密钥）：

1. 输入“查询北京天气，再计算 12 × 8”，检查工具参数、结果 96、逐字回复与轮次编号。
2. 点击模拟邮件示例发送，检查弹窗参数；分别批准和拒绝，确认执行结果一致。
3. 再次发起审核并等待 120 秒，应自动拒绝；然后再次发送问题，确认会话没有锁死。
4. 输入“调用 slow_tool 测试超时降级”，约三秒后出现超时结果，模型继续回复。
5. 新建两个会话，分别说明不同昵称并追问；切换和刷新后历史应互不混淆。
6. 生成过程中点击停止或刷新页面，再进入该会话；未完成轮次不应污染后续模型上下文。
7. 停掉后端后发送消息，检查连接错误提示；恢复后重新载入会话并发送。

## Day 7：打包与单端口部署

```powershell
cd week11/frontend
npm ci
npm run build
cd ../backend
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8083
```

构建自动写入 `backend/static`，必须先构建再启动/重启后端。此时只访问 <http://127.0.0.1:8083>，无需启动 Vite，页面与 API 同源。部署时复制 backend（包括 static，不包括本地 venv、数据库和密钥），在目标机器安装依赖并单独配置 `.env`。

当前定位为本机学习应用，无账号认证；session_id 是隔离键，不是权限系统。不要直接开放到公网；公开部署需增加认证、会话所有权检查、限流与 HTTPS。审核 Future 和运行锁在进程内，使用默认单 worker；多 worker 需要 Redis 等共享协调。若配置 Nginx，SSE 路径需 `proxy_buffering off`、`proxy_cache off`、`proxy_read_timeout 300s`。原生 EventSource 使用 GET，问题会出现在 URL 中，生产环境应改为 POST 创建任务、GET 使用随机任务 ID 订阅，并避免记录敏感查询参数。

`npm run preview` 只预览前端构建产物，没有配置后端 API 代理，不能替代上面的单端口联调方式。需要完整功能时使用 `npm run dev` 或直接访问 FastAPI 托管的 8083 页面。

## 常见问题

| 现象 | 检查与处理 |
| --- | --- |
| Vite 启动失败、Node API 不兼容 | 执行 `node --version`，使用 Node 20.19+；本次构建使用 Node 24，系统旧版 Node 14 不适用 |
| 页面提示尚未配置模型 | 检查 `backend/.env` 中的密钥是否非空，重启后端，再刷新页面 |
| 已配置密钥但调用失败 | 检查后端日志、密钥有效性、模型名称、接口地址和网络；健康检查不验证这些内容 |
| 8083 根路径返回 404 | 先在 frontend 执行 `npm run build`，确认生成 `backend/static/index.html`，然后重启后端 |
| 8003 启动提示端口占用 | Vite 开启了 `strictPort`，不会自动换端口；关闭占用 8003 的旧服务后重试 |
| 流中断后没有自动恢复 | 这是防重复执行设计；重新载入会话核对历史后，再提交新任务 |
| 审核返回 409 | 审核可能已处理、超时、取消，或与请求中的会话不匹配；检查当前轮次状态 |
| 切换地址后会话列表为空 | 浏览器按来源隔离 localStorage，回到原来的主机名和端口查看 |

## 当前边界与后续扩展

默认数据库在 `backend/agent_memory.db`，可用 `AGENT_DB_PATH` 调整。前端会话索引保存在当前浏览器 localStorage，清除浏览器数据后不会自动找回会话列表；SQLite 数据仍在。当前完整读取会话历史，长对话的上下文压缩、跨设备会话列表和执行中断后的续传留待后续扩展。
