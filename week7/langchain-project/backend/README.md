# Week 7 Chat Agent Backend

`week7/langchain-project/backend` 是基于 FastAPI 的 Agent 后端，负责用户注册登录、会话管理、聊天历史、SSE 流式推送，以及 LangChain Agent 的用户隔离上下文注入。

## 运行端口

- 本地 / 容器后端端口：`8002`
- Swagger 文档：`http://localhost:8002/docs`

## 主要能力

- JWT 注册与登录
- 用户级会话管理
- 用户级聊天记录隔离
- LangChain Agent 流式响应
- SSE 推送 `thinking / tool_result / token / final / done`
- 工具调用 timeout + retry

## 主要接口

### 认证

- `POST /register`
- `POST /token`
- `GET /me`

### 会话

- `GET /sessions`
- `POST /sessions`
- `DELETE /sessions/{session_id}`

### 聊天

- `GET /history?session_id=...`
- `POST /chat/stream`

## SSE 说明

`POST /chat/stream` 返回类型为：

```text
text/event-stream
```

事件类型包括：

- `thinking`
- `tool_result`
- `retry`
- `token`
- `final`
- `done`
- `error`

## 用户隔离设计

后端会在调用 Agent 前注入当前用户上下文，包括：

- `username`
- `user_id`
- 当前 `session title`
- 当前会话最近历史消息

这样可以确保：

- 不同用户不会串聊天记录
- 不同会话上下文隔离
- Agent 回答能够感知当前登录用户

## 工具稳定性保护

当前版本已经对工具层做了统一包装：

- 工具调用支持超时
- 超时后自动重试
- 异常和超时会推送 `retry` 事件到前端工具面板

相关环境变量：

```env
AGENT_TIMEOUT_SECONDS=60
TOOL_TIMEOUT_SECONDS=8
TOOL_RETRY_COUNT=2
```

## 本地开发

```powershell
cd E:\my\ai-fullstack-journey\week7\langchain-project\backend
Copy-Item .env.example .env
```

然后把 `.env` 里的 `DEEPSEEK_API_KEY` 改成真实值，再执行：

```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

## 环境变量

`backend/.env` 至少需要：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
SECRET_KEY=change-this-secret-in-production
DATABASE_URL=sqlite+aiosqlite:////app/data/app.db
AGENT_TIMEOUT_SECONDS=60
TOOL_TIMEOUT_SECONDS=8
TOOL_RETRY_COUNT=2
```

## Docker

`backend/Dockerfile` 会把服务暴露在容器 `8002` 端口。

数据目录约定：

- SQLite：`/app/data/app.db`

在 `docker-compose.yml` 中，宿主机会把：

```yaml
./data:/app/data
```

挂载到容器中，保证聊天数据持久化。

## 常见问题

### 1. 启动时报缺少 `DEEPSEEK_API_KEY`

- **原因**：`backend/.env` 未配置
- **建议**：先复制 `.env.example` 再填真实 key

### 2. 登录接口返回 401

- **原因**：用户名或密码错误
- **建议**：检查注册是否成功，或清空旧 token 重新登录

### 3. SSE 没有流式输出

- **原因**：代理层缓冲、前端未按流读取、或异常被提前中断
- **建议**：先直接检查 FastAPI `/chat/stream` 返回头是否为 `text/event-stream`

### 4. 容器启动了但前端全是 502

- **原因**：后端还没通过健康检查
- **建议**：

```bash
docker compose ps
docker compose logs --tail=200 backend
```
