# Week 7 - Chat Agent 项目（FastAPI + LangChain + SSE + Docker）

Week 7 的目标不再是传统 RAG 上传问答，而是做一套真正可以“看见 Agent 思考过程”的聊天应用。这个项目基于 `week7/langchain-demo/agent_day3.py` 的流式 Agent 能力继续扩展，在 `week7/langchain-project` 中拆成前后端两部分，并支持 `Docker + Nginx + 子路径部署`。

最终目标地址：

- 线上访问：`https://qishuixian.com/chatAgent/`
- 前端宿主机端口：`8082`
- 后端宿主机端口：`8002`

## 项目概览

这一周的核心能力包括：

- 用户注册 / 登录
- 会话创建、切换、删除
- 基于 LangChain Agent 的流式对话
- 前端实时展示 Agent 的工具调用过程
- SSE 推送最终回答与打字机效果
- 按用户隔离会话和聊天记录
- 工具调用超时与重试保护
- 通过 Docker、Docker Compose、Nginx 完成 `/chatAgent/` 子路径部署

## 技术栈

### 前端

- **框架**：Vue 3
- **UI 组件库**：Element Plus
- **Markdown 渲染**：Marked + marked-highlight
- **代码高亮**：Highlight.js
- **构建工具**：Vite
- **通信方式**：SSE

### 后端

- **框架**：FastAPI
- **认证**：JWT
- **数据库**：SQLite + SQLAlchemy + aiosqlite
- **Agent 编排**：LangChain `create_agent`
- **模型接入**：DeepSeek（通过 `langchain-openai`）
- **稳定性保护**：工具级 timeout + retry

### 部署

- **容器化**：Docker
- **编排**：Docker Compose
- **反向代理**：Nginx
- **访问路径**：`/chatAgent/`

## 核心功能

### 1. 用户认证

- 支持注册与登录
- 使用 JWT 作为访问令牌
- 所有会话和聊天接口都要求鉴权
- 聊天记录、会话列表、工具事件都按用户隔离

### 2. 会话管理

- 左侧提供会话列表
- 支持新建会话
- 支持切换不同会话
- 支持删除会话
- 默认按最近更新时间排序

### 3. Agent 实时流式对话

- 前端通过 `POST /api/chat/stream` 发起请求
- 后端使用 `StreamingResponse` 返回 `text/event-stream`
- 前端实时消费 `token` 事件实现打字机效果
- 最终回答会以 `final` 事件再次收口

### 4. 工具调用面板

后端 SSE 会返回以下事件类型：

- `thinking`：Agent 决定调用哪个工具、参数是什么
- `tool_result`：工具执行结果
- `retry`：超时或异常后的保护性提示
- `token`：模型生成中的文本片段
- `final`：最终完整回答
- `done`：本次流结束
- `error`：中途异常

前端右侧工具面板会实时展示 `thinking / tool_result / retry` 这些过程事件。

### 5. 用户上下文隔离

后端在调用 Agent 前会注入：

- 当前用户 `username`
- 当前用户 `user_id`
- 当前会话 `title`
- 当前会话最近历史消息

这样可以保证：

- 不同用户之间不会串聊天记录
- 不同会话之间上下文独立
- Agent 回答时能知道“当前是谁、当前在哪个会话里”

### 6. 超时与重试

当前实现重点放在工具层：

- 每个工具调用都走统一 timeout 包装
- 超时后会自动重试指定次数
- 超时和异常会通过 SSE 的 `retry` 事件推送给前端

## 项目结构

```text
week7/langchain-project/
├─ backend/
│  ├─ main.py                   # FastAPI 主应用，包含登录、会话、历史、SSE Agent
│  ├─ auth.py                   # JWT 认证与密码哈希逻辑
│  ├─ database.py               # 数据库模型与初始化
│  ├─ dependencies.py           # 数据库依赖注入
│  ├─ requirements.txt          # 后端依赖
│  ├─ Dockerfile                # 后端镜像构建文件
│  └─ .env.example             # 后端环境变量示例
├─ frontend/
│  ├─ src/
│  │  ├─ App.vue
│  │  ├─ components/
│  │  │  ├─ LoginForm.vue       # 登录 / 注册
│  │  │  ├─ Sidebar.vue         # 会话侧边栏
│  │  │  ├─ ChatArea.vue        # 聊天区 + SSE 消费
│  │  │  ├─ MessageList.vue     # 消息列表
│  │  │  ├─ ChatInput.vue       # 发送输入框
│  │  │  └─ ToolPanel.vue       # 工具调用面板
│  │  └─ styles/
│  ├─ .env.development          # 开发环境配置
│  ├─ .env.production           # 生产构建基路径配置（/chatAgent/）
│  ├─ Dockerfile                # 前端镜像构建文件
│  ├─ nginx.chat-agent.conf     # 前端容器 Nginx 配置
│  └─ package.json              # 前端依赖与脚本
├─ docker-compose.yml           # 本地 / 服务器编排
├─ nginx.chatagent.conf         # 宿主机 Nginx 子路径代理片段
├─ .gitignore
└─ README.md
```

## 本地开发

### 前置要求

- Python 3.10+
- Node.js
- npm
- Docker + Docker Compose（可选）

说明：

- 当前这台本地环境是 `Node 14.20.0`
- 为了保证能在当前环境完成前端打包，`frontend/package.json` 的 `build` 使用的是 `vite build`
- 如果你后续升级到 Node 16+ 或 18+，可以再把 `vue-tsc` 类型检查加回构建链

## 后端启动

```powershell
cd E:\my\ai-fullstack-journey\week7\langchain-project\backend
Copy-Item .env.example .env
```

把 `.env` 中的：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

改成真实值后，再启动：

```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

后端地址：

```text
http://localhost:8002
```

接口文档：

```text
http://localhost:8002/docs
```

## 前端启动

```powershell
cd E:\my\ai-fullstack-journey\week7\langchain-project\frontend
npm install
npm run dev
```

前端地址：

```text
http://localhost:8082
```

开发环境下，Vite 会把 `/api` 代理到：

```text
http://127.0.0.1:8002
```

## 本地联调说明

本地前后端启动后，完整访问链路如下：

```text
浏览器
  -> http://localhost:8082
Vite dev server
  -> /api/* 代理到 http://127.0.0.1:8002
FastAPI
  -> /token /register /sessions /history /chat/stream
```

你可以按下面顺序验证：

1. 打开 `http://localhost:8082`
2. 注册一个账号并登录
3. 左侧确认能自动创建默认会话
4. 输入问题并发送
5. 观察右侧工具调用面板是否出现 `thinking` 和 `tool_result`
6. 观察中间聊天区是否出现打字机效果和最终回答

## SSE 接口说明

### 请求地址

```text
POST /api/chat/stream
```

### 请求体

```json
{
  "message": "广州天气怎么样？另外帮我算 12 * 5，并查一下 LangGraph",
  "session_id": "会话ID"
}
```

### 返回类型

```text
text/event-stream
```

### SSE 示例

```text
data: {"type":"thinking","content":"决定调用工具 [get_weather]，参数: {'city':'广州'}"}

data: {"type":"tool_result","content":"工具 [get_weather] 返回: 广州 今天是晴天，25度。"}

data: {"type":"token","content":"广州今天"}

data: {"type":"final","content":"广州今天晴天，25度。12 * 5 = 60 ..."}

data: {"type":"done","content":"[DONE]"}
```

## Docker 本地启动

在项目根目录执行：

```powershell
cd E:\my\ai-fullstack-journey\week7\langchain-project
docker compose up --build -d
```

启动后访问：

- 前端：`http://localhost:8082/chatAgent/`
- 后端：`http://localhost:8002`

### `docker-compose.yml` 说明

- 前端：`8082:80`
- 后端：`8002:8002`
- SQLite 数据目录：`./data:/app/data`
- 后端环境变量：`./backend/.env`

## 生产部署架构

线上访问链路如下：

```text
浏览器
  -> https://qishuixian.com/chatAgent/
宿主机 Nginx
  -> 前端容器 127.0.0.1:8082
前端容器 Nginx
  -> /chatAgent/ 静态资源
  -> /api/ 转发到 backend:8002
后端容器 FastAPI
  -> Agent SSE / 登录 / 会话 / 历史接口
```

## 镜像构建

```powershell
cd E:\my\ai-fullstack-journey\week7\langchain-project
docker build -t chat-agent-backend:latest -f backend/Dockerfile backend/
docker build -t chat-agent-frontend:latest -f frontend/Dockerfile frontend/
```

如果你要完全对齐 `week5/rag_project` 的发布方式，建议构建镜像后先导出：

```powershell
docker save chat-agent-backend:latest -o chat-agent-backend.tar
docker save chat-agent-frontend:latest -o chat-agent-frontend.tar
```

## 服务器部署步骤

部署方式按 `week5/rag_project` 保持一致：  
先在本地整理项目目录，打包压缩文件上传服务器；然后在服务器上解压、补环境变量、启动 Docker。

### Step 1：本地整理发布目录

建议先确认下面这些内容已经准备好：

- `backend/.env` 已填写真实的 `DEEPSEEK_API_KEY`
- `frontend` 已能本地完成 `npm run build`
- `docker-compose.yml`、前后端 `Dockerfile`、Nginx 配置文件都在项目目录中

建议发布目录结构如下：

```text
langchain-project/
├─ backend/
│  ├─ .env
│  ├─ auth.py
│  ├─ database.py
│  ├─ dependencies.py
│  ├─ Dockerfile
│  ├─ main.py
│  └─ requirements.txt
├─ frontend/
│  ├─ Dockerfile
│  ├─ nginx.chat-agent.conf
│  ├─ package.json
│  ├─ package-lock.json
│  ├─ src/
│  └─ ...
├─ docker-compose.yml
├─ nginx.chatagent.conf
└─ README.md
```

### Step 2：本地打包压缩文件

如果你想和 week5 一样走“先打包再上传”的方式，可以直接在 `week7` 目录下把整个 `langchain-project` 打成压缩包。

Windows 下可以直接手动压缩成 `rar` 或 `zip`。  
如果本机安装了 WinRAR，也可以命令行打包：

```powershell
cd E:\my\ai-fullstack-journey\week7
rar a langchain-project.rar .\langchain-project\
```

如果没有 `rar` 命令，用 PowerShell 自带压缩也可以：

```powershell
cd E:\my\ai-fullstack-journey\week7
Compress-Archive -Path .\langchain-project\* -DestinationPath .\langchain-project.zip -Force
```

### Step 3：上传到服务器

例如上传到服务器部署目录：

```bash
scp langchain-project.rar root@<SERVER_IP>:/opt/
```

如果你上传的是 zip，则改成：

```bash
scp langchain-project.zip root@<SERVER_IP>:/opt/
```

如果你还按 week5 的镜像导出方案走，也一并上传：

```bash
scp chat-agent-backend.tar root@<SERVER_IP>:/opt/
scp chat-agent-frontend.tar root@<SERVER_IP>:/opt/
scp docker-compose.prod.yml root@<SERVER_IP>:/opt/
```

### Step 4：服务器解压

登录服务器后执行：

```bash
ssh root@<SERVER_IP>
cd /opt
```

如果上传的是 `rar`：

```bash
mkdir -p /opt/chat-agent
unrar x langchain-project.rar /opt/chat-agent/
```

如果上传的是 `zip`：

```bash
mkdir -p /opt/chat-agent
unzip langchain-project.zip -d /opt/chat-agent
```

解压后，建议确认实际目录层级，保证最终启动目录里能直接看到：

- `backend/`
- `frontend/`
- `docker-compose.yml`

如果解压后多了一层目录，比如：

```text
/opt/chat-agent/langchain-project/
```

那就进入这一层再启动：

```bash
cd /opt/chat-agent/langchain-project
```

### Step 5：检查后端环境变量

确认服务器上的：

```text
backend/.env
```

至少包含：

```env
DEEPSEEK_API_KEY=your_real_key
SECRET_KEY=change-this-secret-in-production
DATABASE_URL=sqlite+aiosqlite:////app/data/app.db
AGENT_TIMEOUT_SECONDS=60
TOOL_TIMEOUT_SECONDS=8
TOOL_RETRY_COUNT=2
```

### Step 6：加载镜像并启动容器

如果你上传了导出的镜像包，先加载：

```bash
docker load -i /opt/chat-agent-backend.tar
docker load -i /opt/chat-agent-frontend.tar
```

然后进入最终项目目录，使用生产编排启动：

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
docker compose ps
docker compose logs --tail=200 backend
docker compose logs --tail=200 frontend
```

## Nginx 配置说明

### 1. 前端容器内 Nginx

[frontend/nginx.chat-agent.conf](E:\my\ai-fullstack-journey\week7\langchain-project\frontend\nginx.chat-agent.conf) 负责：

- `/chatAgent/` 静态资源访问
- `/api/` 转发到 `backend:8002`

前端构建产物被复制到：

```text
/usr/share/nginx/html/chatAgent/
```

### 2. 宿主机 Nginx 反向代理

可以直接参考：

[nginx.chatagent.conf](E:\my\ai-fullstack-journey\week7\langchain-project\nginx.chatagent.conf)

宿主机完整示例：

```nginx
server {
    listen 80;
    server_name qishuixian.com www.qishuixian.com;

    location = /chatAgent {
        return 302 /chatAgent/;
    }

    location /chatAgent/ {
        proxy_pass http://127.0.0.1:8082/chatAgent/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

修改后记得执行：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 常见问题与排查

### 1. 登录成功后会话列表为空

- **原因**：当前账号第一次登录，还没有任何会话
- **当前处理**：前端会自动调用创建会话接口
- **检查项**：
  - `/api/sessions` 是否返回空数组
  - `/api/sessions` 的 POST 是否成功

### 2. SSE 接口没有实时返回

- **原因**：代理层缓冲了响应
- **当前处理**：后端和前端容器 Nginx 都已经加了禁缓冲相关设置
- **检查项**：
  - FastAPI 是否返回 `text/event-stream`
  - Nginx 是否配置了 `proxy_buffering off`
  - 前端是否逐段读取 `ReadableStream`

### 3. 页面能打开，但接口 401

- **原因**：本地 token 丢失或过期
- **建议**：
  - 清掉浏览器 `localStorage`
  - 重新登录
  - 检查 `Authorization: Bearer <token>` 是否带上

### 4. Agent 提示缺少 `DEEPSEEK_API_KEY`

- **原因**：后端 `.env` 未配置或启动目录不对
- **检查项**：
  - `backend/.env` 是否存在
  - 是否包含 `DEEPSEEK_API_KEY=...`
  - 后端是否从 `backend` 目录启动

### 5. 工具面板没有内容，但最终回答出来了

- **原因**：当前回答可能不需要工具，模型直接给了最终结果
- **说明**：这是正常情况，不一定每次都触发工具调用

### 6. `docker compose up -d` 后前端接口 502

- **原因**：后端还没通过健康检查，前端容器已启动但代理不到后端
- **排查方式**：

```bash
docker compose ps
docker compose logs --tail=200 backend
docker compose logs --tail=200 frontend
```

### 7. 访问 `/chatAgent` 出现静态资源 404

- **原因**：前端打包基路径、容器 Nginx、宿主机 Nginx 三处不一致
- **检查项**：
  - `frontend/.env.production` 是否为 `VITE_BASE_URL=/chatAgent/`
  - 前端 Dockerfile 是否复制到 `/usr/share/nginx/html/chatAgent/`
  - 宿主机是否代理到 `127.0.0.1:8082/chatAgent/`

### 8. 前端本地构建时报 Node 版本相关错误

- **原因**：当前机器 Node 版本偏低
- **当前情况**：截至 2026-09-01，这台机器本地是 `Node 14.20.0`
- **当前处理**：已把构建脚本收敛为 `vite build`
- **建议**：后续升级到 Node 16+ 或 18+，再补回更严格的类型构建链

## 学习要点

1. **Agent 可视化**：不是只拿最终答案，更要把工具调用过程流给前端。
2. **用户隔离**：会话、历史、工具事件都要绑定用户身份。
3. **SSE 消费**：前端不仅要接流，还要处理 `thinking / tool_result / token / final / done` 多种事件。
4. **子路径部署**：`/chatAgent/` 场景下，Vite base、容器 Nginx、宿主机 Nginx 必须统一。
5. **稳定性保护**：工具执行要考虑超时、异常和重试，而不是只在 happy path 下跑通。

## 作者

- 开发者：戚水仙
- 时间：2026-09
- 项目：AI 全栈学习之旅 - Week 7
