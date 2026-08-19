# Week 5 - RAG 知识库问答项目（Docker + Nginx + 域名部署）

基于前几周的聊天应用继续演进，Week 5 的目标是把项目升级为一个支持用户登录、文件上传、向量检索、RAG 问答，并且可以通过 `qishuixian.com/ask` 对外访问的完整应用。

## 项目概览

这一周的核心不再只是“聊天”，而是围绕“用户自己的知识库”构建一套完整流程：

- 用户注册 / 登录
- 上传 PDF 文件
- 自动切分文档并写入 ChromaDB
- 提问时默认检索当前用户上传的全部文件
- 删除文件时同步删除对应向量数据
- 通过 Docker、Docker Compose、Nginx 完成部署

最终部署目标：

- 访问地址：`https://qishuixian.com/ask`
- 前端宿主机端口：`8081`
- 后端宿主机端口：`8001`
- 服务器上传文件目录：`ask`

## 技术栈

### 前端

- **框架**：Vue 3 + TypeScript
- **UI 组件库**：Element Plus
- **状态管理**：Pinia
- **Markdown 渲染**：Marked + marked-highlight
- **代码高亮**：Highlight.js
- **构建工具**：Vite

### 后端

- **框架**：FastAPI
- **认证**：JWT
- **数据库**：SQLite + SQLAlchemy + aiosqlite
- **文件处理**：aiofiles + PyPDFLoader
- **向量数据库**：ChromaDB
- **Embedding**：HuggingFace Embeddings（`BAAI/bge-small-zh-v1.5`）
- **大模型**：DeepSeek
- **RAG 组件**：LangChain

### 部署

- **容器化**：Docker
- **编排**：Docker Compose
- **反向代理**：Nginx
- **访问路径**：`/ask`
- **目标域名**：`qishuixian.com`

## 核心功能

### 1. 用户认证

- 支持注册与登录
- 使用 JWT 作为访问令牌
- 所有文件接口和问答接口都要求鉴权
- 文件和聊天记录都按当前用户隔离

### 2. 文件管理

- 左侧从“会话列表”改成“文件管理列表”
- 支持上传 PDF 文件
- 支持查看当前用户上传的文件列表
- 支持删除文件
- 删除文件时同步从 ChromaDB 中移除对应向量

### 3. RAG 问答

- 用户提问时默认检索“当前用户的全部文件”
- 检索结果会拼接成上下文发送给模型
- 使用流式响应返回回答
- 历史消息保存在数据库中

### 4. 上传体验

- 文件上传限制为 PDF
- 文件大小限制为 10MB
- 上传时有全局 Loading 遮罩
- 上传完成后自动刷新文件列表

### 5. 部署能力

- 前后端分别构建 Docker 镜像
- Compose 支持本地开发和服务器部署两种方式
- 前端构建后以 `/ask/` 为静态资源基路径
- 宿主机 Nginx 把 `/ask/` 转发到前端容器，把 `/api/` 转发到后端容器

## 项目结构

```text
week5/rag_project/
├─ backend/
│  ├─ main.py                   # FastAPI 主应用，包含问答、文件管理、历史消息等接口
│  ├─ auth.py                   # JWT 认证与密码哈希逻辑
│  ├─ database.py               # 数据库模型与初始化
│  ├─ dependencies.py           # 数据库依赖注入
│  ├─ requirements.txt          # 后端依赖
│  ├─ Dockerfile                # 后端镜像构建文件
│  └─ README.md                 # 后端说明文档
├─ frontend/
│  ├─ src/
│  │  ├─ App.vue
│  │  ├─ components/
│  │  │  ├─ LoginForm.vue       # 登录/注册组件
│  │  │  ├─ Sidebar.vue         # 文件管理侧边栏
│  │  │  ├─ ChatArea.vue        # RAG 问答主区域
│  │  │  ├─ MessageList.vue     # 消息列表
│  │  │  └─ ChatInput.vue       # 输入框组件
│  │  ├─ stores/
│  │  └─ styles/
│  ├─ frontend-ask.conf         # 前端容器 Nginx 配置
│  ├─ nginx.conf                # 前端开发/容器代理配置
│  ├─ .env.production           # 生产构建基路径配置（/ask/）
│  ├─ Dockerfile                # 前端镜像构建文件
│  └─ README.md                 # 前端说明文档
├─ Dockerfile.backend           # 根级后端镜像构建
├─ Dockerfile.frontend          # 根级前端镜像构建
├─ docker-compose.yml           # 本地开发编排
├─ docker-compose.prod.yml      # 生产部署编排
├─ nginx.conf                   # 根级 Nginx 代理配置
└─ README.md                    # 本文档
```

## 本地开发

### 前置要求

- Python 3.11+
- Node.js 18+
- npm
- Docker + Docker Compose（可选）

### 后端启动

```bash
cd backend

python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
# source venv/bin/activate

python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

后端地址：

```text
http://localhost:8001
```

接口文档：

```text
http://localhost:8001/docs
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端地址：

```text
http://localhost:5173
```

开发环境下，Vite 会把 `/api` 代理到：

```text
http://127.0.0.1:8001
```

## Docker 本地联调

在项目根目录执行：

```bash
cd week5/rag_project
docker compose up --build -d
```

启动后访问：

- 前端：`http://localhost:8081/ask/`
- 后端：`http://localhost:8001`

### `docker-compose.yml` 说明

本地联调使用如下约定：

- 前端：`8081:80`
- 后端：`8001:8001`
- SQLite 数据目录：`./data:/app/data`
- 上传文件目录：`./ask:/app/uploads`

这样本地上传的 PDF 会直接落在项目目录下的 `ask/` 文件夹中。

## 生产部署架构

部署后的访问链路如下：

```text
浏览器
  -> https://qishuixian.com/ask
宿主机 Nginx
  -> 前端容器 localhost:8081
  -> 后端容器 localhost:8001
Docker 容器
  ├─ ask-frontend:80
  └─ ask-backend:8001
```

## 生产镜像构建

### 方式 1：使用根目录 Dockerfile

```bash
cd week5/rag_project
docker build -t ask-backend:latest -f Dockerfile.backend .
docker build -t ask-frontend:latest -f Dockerfile.frontend .
```

### 方式 2：使用子目录 Dockerfile

```bash
cd week5/rag_project
docker build -t ask-backend:latest -f backend/Dockerfile backend/
docker build -t ask-frontend:latest -f frontend/Dockerfile frontend/
```

## 生产部署步骤

### Step 1：导出镜像

```bash
docker save ask-backend:latest -o ask-backend.tar
docker save ask-frontend:latest -o ask-frontend.tar
```

### Step 2：上传到服务器

```bash
scp ask-backend.tar root@<SERVER_IP>:/opt/ask/
scp ask-frontend.tar root@<SERVER_IP>:/opt/ask/
scp docker-compose.prod.yml root@<SERVER_IP>:/opt/ask/docker-compose.yml
```

### Step 3：服务器加载并启动

```bash
ssh root@<SERVER_IP>
cd /opt/ask

docker load -i ask-backend.tar
docker load -i ask-frontend.tar

docker compose up -d
docker compose ps
docker compose logs -f
```

建议服务器目录结构：

```text
/opt/ask/
├─ docker-compose.yml
├─ data/
└─ ask/
```

其中：

- `data/` 保存 SQLite 数据
- `ask/` 保存用户上传的 PDF 文件

### `docker-compose.prod.yml` 说明

生产环境使用如下约定：

- 后端镜像：`ask-backend:latest`
- 前端镜像：`ask-frontend:latest`
- 前端端口：`8081`
- 后端端口：`8001`
- 上传目录：`./ask:/app/uploads`

## Nginx 配置说明

### 1. 前端容器内 Nginx

前端构建产物被复制到：

```text
/usr/share/nginx/html/ask
```

前端容器通过 `frontend/frontend-ask.conf` 提供：

- `/ask/` 静态页面访问
- `/api/` 转发到 `backend:8001`

### 2. 宿主机 Nginx 反向代理示例

可以在服务器上配置：

```nginx
server {
    listen 80;
    server_name qishuixian.com www.qishuixian.com;
    client_max_body_size 10M;

    location /ask/ {
        proxy_pass http://127.0.0.1:8081/ask/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

这样浏览器访问：

```text
https://qishuixian.com/ask
```

即可进入前端页面，而前端内部请求 `/api/*` 时会由 Nginx 转发到 FastAPI。

## 环境变量说明

### 后端 `.env`

至少需要：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
SECRET_KEY=change-this-secret-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 前端 `.env.production`

```env
VITE_BASE_URL=/ask/
```

这个配置用于保证打包后的静态资源、路由路径都以 `/ask/` 为前缀。

## 常见问题与排查

### 1. 注册接口返回 500

- **原因**：密码哈希方案或依赖不兼容
- **当前处理**：项目已改为 `pbkdf2_sha256`，不再依赖 `bcrypt`
- **建议**：重新执行 `pip install -r requirements.txt`

### 2. 上传 PDF 时提示 `pypdf package not found`

- **原因**：`PyPDFLoader` 运行时依赖的是 `pypdf`，仅安装 `PyPDF2` 不足以完成当前版本的 PDF 解析
- **当前处理**：已在 `backend/requirements.txt` 中补充：

```text
pypdf==5.0.0
```

- **建议**：修改依赖后重新构建后端镜像：

```bash
docker compose build backend
docker compose up -d
```

### 3. 上传 PDF 很久没有响应

- **原因**：后端需要完成 PDF 解析、文本切分、Embedding 计算、向量入库
- **当前处理**：前端已增加全局 Loading
- **建议**：首次运行时，Embedding 模型下载可能更慢

### 4. 访问 `/ask` 出现静态资源 404

- **原因**：前端打包基路径不是 `/ask/`
- **检查项**：
  - `frontend/.env.production` 是否为 `VITE_BASE_URL=/ask/`
  - Dockerfile 是否把构建产物复制到了 `/usr/share/nginx/html/ask`
  - Nginx 是否使用 `/ask/` 路由

### 5. 文件删除后问答还能检索到旧内容

- **原因**：删除时没有同步清理向量库
- **当前实现**：后端会按 `user_id + file_id` 删除 ChromaDB 元数据对应的向量
- **建议**：如果容器里缓存了旧数据，检查是否挂载了正确的数据目录

### 6. 宿主机 Nginx 无法访问容器服务

- **原因**：反向代理地址写成了容器名，或者端口写错
- **建议**：宿主机 Nginx 使用 `127.0.0.1:8081` 和 `127.0.0.1:8001`，不要直接写 Docker 网络中的服务名

### 7. 上传文件时出现 413 Request Entity Too Large

- **原因**：Nginx 默认允许上传的请求体较小，PDF 上传会先在代理层被拦截，导致请求还没到 FastAPI 就返回 `413`
- **当前处理**：已在前端容器 Nginx 配置 `frontend/frontend-ask.conf` 中增加：

```nginx
client_max_body_size 10M;
```

- **注意**：修改 Nginx 配置后需要重新构建并启动前端容器：

```bash
docker compose build frontend
docker compose up -d
```

### 8. `docker compose up -d` 后前端接口全部 502

- **现象**：前端页面能打开，但 `/api/files`、`/api/history`、`/api/token` 等接口全部返回 `502 Bad Gateway`
- **原因**：前端容器已经启动，但后端容器此时可能仍在加载依赖或模型，Nginx 代理到 `backend:8001` 时会出现短暂连接失败
- **排查方式**：

```bash
docker compose ps
docker compose logs --tail=200 frontend
docker compose logs --tail=200 backend
```

- **当前处理**：已在 `docker-compose.yml` 和 `docker-compose.prod.yml` 中为 backend 增加健康检查，并让 frontend 依赖 `service_healthy` 后再启动
- **补充说明**：如果后端首次启动需要加载模型或初始化向量库，健康检查缓冲时间需要足够长；当前配置已将 `start_period` 调整为 `60s`
- **建议**：首次启动完成后刷新一次页面；如果仍有异常，再检查 backend 日志是否还在加载模型或是否启动失败

### 9. 服务器上上传文件丢失

- **原因**：没有把宿主机目录挂载到 `/app/uploads`
- **建议**：确认 `docker-compose.prod.yml` 中使用了：

```yaml
- ./ask:/app/uploads
```

## 学习要点

1. **用户级 RAG 设计**：文件、向量、聊天记录都要绑定用户身份，避免数据串用。
2. **删除一致性**：业务库删文件不够，还要同步删向量库中的对应分片。
3. **子路径部署**：当前端挂在 `/ask/` 下时，Vite `base`、容器 Nginx、宿主机 Nginx 都要统一。
4. **Docker 卷挂载**：上传目录和 SQLite 数据目录都应该持久化，否则容器重启会丢数据。
5. **部署链路排查**：优先按“浏览器 -> 宿主机 Nginx -> Docker 端口 -> 容器日志”的顺序定位问题。

## 许可证

MIT License

## 作者

- 开发者：戚水仙
- 时间：2026-08
- 项目：AI 全栈学习之旅 - Week 5
