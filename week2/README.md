# Week 2 - AI 聊天应用（全栈实现）

一个功能完整的 AI 聊天应用，支持用户认证、多会话管理、实时通信等功能。

## 项目概述

基于 FastAPI + Vue 3 + WebSocket 的智能聊天应用，支持多会话管理、流式输出、Markdown 渲染。

### 技术栈

**前端：**
- Vue 3 (Composition API)
- TypeScript
- Vite
- Vitest (单元测试)
- Marked.js (Markdown 渲染)

**后端：**
- FastAPI (Python Web 框架)
- SQLAlchemy (ORM)
- SQLite + aiosqlite (异步数据库)
- JWT (身份认证)
- WebSocket (实时通信)
- DeepSeek API (AI 对话)

## 功能特性

### ✅ 用户认证
- 用户注册/登录
- JWT Token 认证
- 所有 API 接口鉴权保护

### ✅ 多会话管理
- 创建、切换、删除会话
- 会话自动命名（根据第一条消息）
- 会话编辑重命名
- 会话置顶功能（📌）
- 会话搜索/过滤
- 会话导出（JSON/Markdown 格式）

### ✅ 聊天功能
- 流式响应（SSE）
- Markdown 渲染
- 消息历史记录持久化
- 停止生成功能
- 自动滚动到底部

### ✅ 实时通信
- WebSocket 支持
- 多用户在线状态
- 实时消息广播

### ✅ 用户体验
- 组件化设计
- 响应式布局
- 搜索过滤
- 三点菜单操作
- 加载状态提示

## 项目结构

```
week2/
├── backend/                    # 后端代码
│   ├── main.py                # FastAPI 主程序
│   ├── database.py            # 数据库模型
│   ├── auth.py                # 认证逻辑
│   ├── dependencies.py        # 依赖注入
│   ├── migrate_add_pinned.py  # 数据库迁移脚本
│   ├── requirements.txt       # Python 依赖
│   ├── .env                   # 环境变量（需自行创建）
│   └── chat.db               # SQLite 数据库（自动生成）
│
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── components/       # Vue 组件
│   │   │   ├── LoginForm.vue        # 登录/注册表单
│   │   │   ├── Sidebar.vue          # 侧边栏
│   │   │   ├── ChatArea.vue         # 聊天主区域
│   │   │   ├── MessageList.vue      # 消息列表
│   │   │   ├── ChatInput.vue        # 输入框
│   │   │   └── __tests__/           # 组件测试
│   │   ├── App.vue           # 根组件
│   │   └── main.ts          # 入口文件
│   ├── package.json         # 依赖配置
│   └── vite.config.ts       # Vite 配置
│
├── Dockerfile.backend       # 后端 Docker 配置
├── Dockerfile.frontend      # 前端 Docker 配置
├── docker-compose.yml       # Docker Compose 配置
├── nginx.conf              # Nginx 配置
└── README.md               # 项目文档
```

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- npm 或 pnpm

### 1. 后端设置

```bash
# 进入后端目录
cd week2/backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建 .env 文件并配置 API Key
echo "DEEPSEEK_API_KEY=your_api_key_here" > .env

# 运行后端
uvicorn main:app --reload --port 8000
```

后端服务将在 `http://127.0.0.1:8000` 启动

### 2. 前端设置

```bash
# 进入前端目录
cd week2/frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

### 3. 访问应用

打开浏览器访问 `http://localhost:5173`

## API 接口文档

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 用户注册 |
| POST | `/token` | 用户登录 |

### 会话接口

| 方法 | 路径 | 说明 | 需要认证 |
|------|------|------|---------|
| GET | `/sessions` | 获取会话列表 | ✅ |
| POST | `/sessions` | 创建新会话 | ✅ |
| PATCH | `/sessions/{id}` | 更新会话名称 | ✅ |
| PATCH | `/sessions/{id}/pin` | 置顶/取消置顶 | ✅ |
| DELETE | `/sessions/{id}` | 删除会话 | ✅ |
| GET | `/sessions/{id}/export` | 导出会话 | ✅ |

### 聊天接口

| 方法 | 路径 | 说明 | 需要认证 |
|------|------|------|---------|
| POST | `/chat` | 非流式聊天 | ✅ |
| POST | `/chat/stream` | 流式聊天（SSE） | ✅ |
| GET | `/history` | 获取历史记录 | ✅ |

### WebSocket

| 路径 | 说明 |
|------|------|
| `/ws?token={token}` | WebSocket 连接 |

## 数据库模型

### User（用户表）
- `id`: 主键
- `username`: 用户名（唯一）
- `hashed_password`: 密码哈希
- `created_at`: 创建时间

### Session（会话表）
- `id`: 会话 ID（UUID）
- `name`: 会话名称
- `user_id`: 用户 ID（外键）
- `pinned`: 是否置顶（0/1）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### ChatMessage（消息表）
- `id`: 主键
- `role`: 角色（user/assistant）
- `content`: 消息内容
- `session_id`: 会话 ID（外键）
- `user_id`: 用户 ID（外键）
- `created_at`: 创建时间

## Docker 部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# # 停掉并删容器（数据卷保留）
docker-compose down

# 看容器状态
docker compose ps  

# 重启     
docker compose restart    
```

服务将在以下端口启动：
- 前端：`http://localhost:80`
- 后端：`http://localhost:8000`

## 环境变量

### 后端 `.env` 文件

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DATABASE_URL=sqlite+aiosqlite:///./chat.db
```

## 测试

### 前端测试

```bash
cd frontend
npm run test
```

### 后端测试

```bash
cd backend
pytest
```

## 开发日志

### Day 7 - 数据库持久化
- SQLAlchemy + SQLite 集成
- 消息历史记录存储
- 异步数据库操作

### Day 8 - 依赖注入、中间件、WebSocket
- 实现依赖注入模式
- 添加请求日志中间件
- 集成 WebSocket 实时通信

### Day 10 - 用户认证与多会话管理
- JWT 身份认证
- 用户注册/登录
- 多会话管理
- 会话历史记录持久化

### Day 11 - 组件化重构与功能增强
- 前端组件化拆分（5 个组件）
- 会话置顶功能
- 会话搜索/过滤
- 会话导出（JSON/Markdown）
- 会话编辑重命名
- 三点菜单操作
- Token 验证全覆盖

## 常见问题

### Q: 数据库表结构变更如何处理？
A: 使用提供的迁移脚本：
```bash
cd backend
python migrate_add_pinned.py
```

### Q: 前端代理配置在哪里？
A: 查看 `frontend/vite.config.ts` 中的 `server.proxy` 配置

### Q: 如何修改 AI 模型？
A: 在 `backend/main.py` 的 `chat_stream` 函数中修改 `model` 参数

### Q: WebSocket 连接失败怎么办？
A: 检查：
1. Token 是否有效
2. 后端服务是否运行
3. 浏览器控制台是否有错误

## 技术亮点

1. **前后端分离架构** - RESTful API + Vue SPA
2. **异步编程** - FastAPI async/await + SQLAlchemy async
3. **实时通信** - WebSocket + SSE 流式响应
4. **安全认证** - JWT Token + 密码哈希
5. **组件化设计** - Vue 3 Composition API
6. **响应式布局** - CSS Flexbox
7. **数据持久化** - SQLite + ORM
8. **代码质量** - 单元测试 + TypeScript

## 下一步计划

- [ ] 添加消息编辑/删除功能
- [ ] 支持文件上传
- [ ] 添加聊天记录全文搜索
- [ ] 优化移动端体验
- [ ] 添加主题切换（浅色/深色）
- [ ] 集成更多 AI 模型
- [ ] 添加语音输入
- [ ] 实现消息引用/回复

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 作者

- 开发者：戚水仙
- 时间：2026-07
- 项目：AI 全栈学习之旅 - Week 2
