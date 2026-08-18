# Week 4 - AI 聊天应用进阶版（生产部署）

基于 Week3 的 AI 聊天应用，完成全栈容器化、反向代理、域名绑定及生产环境部署。

## 📋 项目概述

本周目标是将 Week3 开发的 AI 聊天应用**部署上线**，支持通过自定义域名公网访问。  
核心任务包括：
- 前端/后端 Docker 镜像构建与优化
- 多服务编排（`docker-compose`）
- Nginx 反向代理（路径路由 `/chat/`、`/api/`、`/ws`）
- 服务器安全组与防火墙配置
- 域名解析与 ICP 备案（中国大陆服务器必备）

## 🛠️ 技术栈

### 前端
- **框架**: Vue 3 + TypeScript
- **UI 库**: Element Plus 2.9.3
- **状态管理**: Pinia 2.3.2
- **代码高亮**: Highlight.js 11.11.1
- **Markdown**: Marked 18.0.7 + marked-highlight 2.2.1
- **拖拽排序**: Sortable.js 1.15.6
- **构建工具**: Vite 8.1.1

### 后端
- **框架**: FastAPI 0.139.2
- **数据库**: SQLite + SQLAlchemy 2.0.51 + aiosqlite 0.22.1
- **认证**: JWT (python-jose 3.5.0)
- **AI 接口**: DeepSeek API (openai 2.48.0)
- **文件处理**: aiofiles 25.1.0

### 部署
- **容器引擎**: Docker + Docker Compose
- **反向代理**: Nginx（宿主机安装）
- **云服务**: 腾讯云轻量应用服务器（Ubuntu 20.04）
- **域名**: `qishuixian.com`（需 ICP 备案）

## 📁 项目结构

```
week4/
├── backend/
│   ├── main.py                    # FastAPI 主应用
│   ├── auth.py                    # JWT 认证逻辑
│   ├── database.py                # SQLAlchemy 数据库模型
│   ├── dependencies.py            # 依赖注入
│   ├── chat.py                    # 聊天基础接口
│   ├── chat_stream.py             # 流式聊天接口
│   ├── chat_managed.py            # 会话管理接口
│   ├── migrate_add_pinned.py      # 数据库迁移脚本
│   ├── Dockerfile                 # 后端镜像构建
│   ├── requirements.txt           # Python 依赖
│   ├── uploads/                   # 上传文件目录
│   └── data/                      # SQLite 数据卷挂载点
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LoginForm.vue      # 登录/注册组件
│   │   │   ├── Sidebar.vue        # 侧边栏组件
│   │   │   ├── ChatArea.vue       # 聊天主区域
│   │   │   ├── MessageList.vue    # 消息列表
│   │   │   └── ChatInput.vue      # 输入框组件
│   │   ├── stores/
│   │   │   └── theme.ts           # 主题状态管理
│   │   ├── styles/
│   │   │   └── global.css         # 全局样式
│   │   ├── App.vue                # 根组件
│   │   └── main.ts                # 入口文件
│   ├── Dockerfile                 # 前端镜像构建（含 Nginx）
│   ├── nginx.conf                 # 前端容器 Nginx 配置
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md                  # 前端开发文档
│
├── Dockerfile.backend             # 根级后端镜像（含 backend/ 上下文）
├── Dockerfile.frontend            # 根级前端镜像（多阶段构建）
├── nginx.conf                     # 生产 Nginx 反向代理配置
├── docker-compose.yml             # 开发环境（本地构建）
├── docker-compose.prod.yml        # 生产环境（直接使用镜像）
├── .env.example                   # 环境变量示例
└── README.md                      # 本文件
```

## 🚀 快速开始（本地开发）

### 前置要求
- Python 3.10+
- Node.js 18+
- npm 或 pnpm
- Docker + Docker Compose（可选，用于容器化开发）

### 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 配置 .env 文件
echo "DEEPSEEK_API_KEY=your_api_key_here" > .env

# 运行后端
uvicorn main:app --reload

```
后端服务：`http://127.0.0.1:8000`

### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

前端服务：`http://localhost:5173`

### Docker 本地开发
```bash
docker compose up --build -d
```
访问地址：
- 前端：http://localhost:8080
- 后端：http://localhost:8000

###  🚢 生产部署（服务器）
## 部署架构

```bash
用户浏览器
    ↓ (http://qishuixian.com/chat)
宿主机 Nginx (监听 80 端口)
    ↓
Docker 容器网络
    ├── frontend (chat-frontend:80)  → 静态文件 /usr/share/nginx/html/chat/
    └── backend  (chat-backend:8000) → FastAPI 服务
```
##  Step 1：本地构建镜像
```bash
# 构建前端镜像（确保 .env.production 中 VITE_BASE_URL=/chat/）
docker build -t chat-frontend:latest -f frontend/Dockerfile frontend/

# 构建后端镜像
docker build -t chat-backend:latest -f backend/Dockerfile backend/

#或者构建所有
docker compose -p chat up --build -d
# 确认镜像
docker images
```
## Step 2：导出并上传到服务器
```bash
# 打包镜像
docker save chat-frontend:latest -o frontend.tar
docker save chat-backend:latest  -o backend.tar

# 上传镜像和配置文件
scp frontend.tar backend.tar root@<SERVER_IP>:/opt/chat/
scp docker-compose.prod.yml    root@<SERVER_IP>:/opt/chat/docker-compose.yml
```
## Step 3：服务器加载并启动
 ```bash
 ssh root@<SERVER_IP>
  cd /opt/chat

  # 加载镜像
  docker load -i backend.tar
  docker load -i frontend.tar

  # 启动服务
  docker compose up -d
  # 重启服务
  docker compose restart
  # 查看日志
  docker compose logs -f
  # 验证
  docker compose ps
  # 停止并移除容器（数据卷保留）
  docker compose down
  # 停止并删除旧容器和旧镜像
  docker compose down --rmi all
  curl http://localhost:8080/chat/   # 应返回 HTML
 ```
## Step 4：配置宿主机 Nginx 反向代理
编辑/etc/nginx/sites-available/chat：
```bash
server {
    listen 80;
    server_name qishuixian.com www.qishuixian.com;

    # ========== 1. 前端页面：指向 chat-frontend (宿主机8080端口) ==========
    location /chat/ {
        proxy_pass http://localhost:8080/;  # 宿主机端口映射
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        try_files $uri $uri/ /chat/index.html;  # 处理前端路由History模式
    }

    # ========== 2. 后端 API：指向 chat-backend (宿主机8000端口) ==========
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # ========== 3. WebSocket ==========
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }

    # ========== 4. 静态文件 ==========
    location /uploads/ {
        proxy_pass http://localhost:8000/uploads/;
        proxy_set_header Host $host;
    }
}
```
 启用站点并重启 Nginx：
 ```bash
sudo nginx -t       # 测试配置语法
sudo systemctl reload nginx  # 重载配置
```

### Step 5：域名解析与安全组

1. **DNS 解析**：在域名注册商（如腾讯云 DNSPod）添加 A 记录：
   - 主机记录：`@` → 服务器公网 IP
   - 主机记录：`www` → 服务器公网 IP
2. **安全组**：在云控制台放行 **TCP 80** 端口（来源 `0.0.0.0/0`）
3. **服务器防火墙**（如有）：`sudo ufw allow 80/tcp`

### Step 6：ICP 备案（中国大陆服务器必须）

- 备案周期：约 10~20 个工作日
- 备案期间域名无法访问，建议暂停 DNS 解析
- 备案通过后恢复解析即可正常访问

## 🧩 常见问题与踩坑记录

### 1. `rolldown` 原生模块缺失（`Cannot find module '@rolldown/binding-linux-x64-musl'`）
- **原因**：Alpine Linux 镜像缺少 musl 预编译绑定。
- **解决**：将基础镜像从 `node:20-alpine` 改为 `node:20-slim`（使用 glibc）。

### 2. 前端容器返回 500 Internal Server Error
- **原因**：容器内部 Nginx 配置未适配 `/chat/` 子路径。
- **解决**：修改容器内 Nginx 配置，设置 `root /usr/share/nginx/html/chat;` 并添加 `try_files` 处理 SPA 路由。

### 3. Nginx 报错 `host not found in upstream "frontend"`
- **原因**：宿主机 Nginx 无法解析 Docker 容器名（`frontend`）。
- **解决**：使用宿主机端口映射（`localhost:8080`）而非容器名。

### 4. 构建时镜像被镜像加速器白名单拦截
- **原因**：服务器配置了公共镜像加速器，但本地镜像未加载成功。
- **解决**：确保 `docker load` 成功，并使用 `docker compose build --no-cache --pull never` 强制使用本地镜像。

### 5. 浏览器访问超时
- **原因**：云服务器安全组未放行 80 端口，或 Ubuntu UFW 防火墙未开启。
- **解决**：在腾讯云安全组添加入方向 TCP:80，并检查 `sudo ufw status`。

## 💡 学习要点

1. **Docker 多阶段构建**：减少最终镜像体积，分离构建环境和运行环境。
2. **Nginx 反向代理**：路径路由（`location /chat/`）、WebSocket 升级、`try_files` 处理 SPA 路由。
3. **Docker 网络**：自定义 bridge 网络实现容器间通信，端口映射与 `expose` 的区别。
4. **环境变量驱动**：通过 `.env.production` 控制 Vite 的 `base` 路径，实现开发/生产差异化。
5. **生产部署流程**：本地构建 → 导出 tar → 服务器加载 → 编排启动。
6. **云服务器网络**：安全组规则、UFW 防火墙、域名解析与 ICP 备案。
7. **错误排查方法论**：从日志入手，逐步缩小范围（容器日志 → Nginx 日志 → 网络连通性）。

## 📜 许可证

MIT License

## 👤 作者

- 开发者：戚水仙
- 时间：2026-08
- 项目：AI 全栈学习之旅 - Week 4