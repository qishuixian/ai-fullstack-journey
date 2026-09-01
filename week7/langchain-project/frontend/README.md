# Week 7 Chat Agent Frontend

`week7/langchain-project/frontend` 是基于 Vue 3 + Element Plus + Vite 的前端界面，负责登录注册、会话切换、实时聊天、SSE 消费、打字机效果，以及工具调用面板展示。

部署目标路径为：

```text
https://qishuixian.com/chatAgent/
```

## 运行端口

- 本地 Vite 开发端口：`8082`
- Docker / Nginx 前端端口：`8082`

## 主要能力

- 登录 / 注册
- 左侧会话列表
- 新建 / 删除 / 切换会话
- 中间聊天区
- SSE 实时流式接收
- 打字机效果
- 右侧工具调用面板

## 页面结构

当前前端布局分为三块：

- 左侧：会话列表
- 中间：聊天主区域
- 右侧：工具调用面板

这样可以同时看到：

- 用户自己发出的消息
- Agent 最终回答
- Agent 中途工具调用和思考过程

## 关键组件

- `src/App.vue`：整体登录态与页面布局
- `src/components/LoginForm.vue`：登录 / 注册页
- `src/components/Sidebar.vue`：会话侧边栏
- `src/components/ChatArea.vue`：聊天区与 SSE 消费主逻辑
- `src/components/MessageList.vue`：消息列表
- `src/components/ChatInput.vue`：输入框
- `src/components/ToolPanel.vue`：工具调用面板

## 本地开发

```powershell
cd E:\my\ai-fullstack-journey\week7\langchain-project\frontend
npm install
npm run dev
```

默认访问：

```text
http://localhost:8082
```

开发环境下通过 Vite 代理把 `/api` 转发到：

```text
http://127.0.0.1:8002
```

## SSE 消费逻辑

前端会请求：

```text
POST /api/chat/stream
```

然后逐段读取 `ReadableStream`，处理这些事件：

- `thinking`：显示到工具面板
- `tool_result`：显示到工具面板
- `retry`：显示到工具面板
- `token`：增量拼接成打字机效果
- `final`：最终落成完整回答
- `done`：结束当前流
- `error`：显示错误信息

## 生产构建路径

生产环境静态资源基路径通过 `frontend/.env.production` 固定为：

```env
VITE_BASE_URL=/chatAgent/
```

因此构建产物会以 `/chatAgent/` 作为资源前缀，适配：

```text
https://qishuixian.com/chatAgent/
```

## Docker

`frontend/Dockerfile` 会：

1. 构建 Vue 前端
2. 将产物复制到容器内 `/usr/share/nginx/html/chatAgent/`
3. 使用 `nginx.chat-agent.conf` 提供 `/chatAgent/` 路径访问
4. 将 `/api/` 转发到 `backend:8002`

## 本地构建说明

截至 `2026-09-01`，当前本机环境还是 `Node 14.20.0`。  
为了保证这台机器上能顺利打包，当前 `package.json` 的 `build` 脚本使用的是：

```json
"build": "vite build --mode production"
```

也就是说：

- 当前可以正常打包
- 但没有把 `vue-tsc` 放进构建前置检查

如果你后续把 Node 升级到 `16+` 或 `18+`，可以再把 `vue-tsc` 类型检查加回去。

## 常见问题

### 1. 页面能打开，但登录接口 401

- **原因**：token 过期或本地 token 不合法
- **建议**：清掉 `localStorage` 后重新登录

### 2. 会话列表不刷新

- **原因**：创建 / 删除会话后没有重新拉取接口或切换当前会话
- **当前实现**：`App.vue` 已在创建、删除、切换后更新当前会话状态

### 3. 右侧工具面板没有内容

- **原因**：这次回答不一定触发工具调用
- **说明**：如果模型直接回答，就只会看到中间聊天结果，不一定有工具事件

### 4. 打字机效果不生效

- **原因**：SSE 被代理缓冲，或后端没有持续返回 `token`
- **建议**：先确认后端接口返回的确实是 `text/event-stream`

### 5. 访问 `/chatAgent` 静态资源 404

- **原因**：`VITE_BASE_URL`、前端容器 Nginx、宿主机 Nginx 三处不一致
- **检查项**：
  - `.env.production` 是否为 `VITE_BASE_URL=/chatAgent/`
  - Dockerfile 是否复制到 `/usr/share/nginx/html/chatAgent/`
  - 宿主机是否代理到 `127.0.0.1:8082/chatAgent/`
