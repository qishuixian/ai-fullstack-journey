# AI Fullstack Journey

从 10 年前端转型 AI 全栈工程师的学习记录。

## 学习日志

### Month 1 · AI 聊天全栈应用

| Day | 主题 | 状态 |
|-----|------|------|
| Day 1 | Python 环境搭建 & DeepSeek API 非流式调用 | ✅ |
| Day 2 | 流式输出（Streaming / SSE） | ✅ |
| Day 3 | 多轮对话上下文管理 | ✅ |
| Day 4 | FastAPI 后端搭建（`/chat` + `/chat/stream`） | ✅ |
| Day 5 | Vue3 前端对接 & 流式渲染（打字机效果） | ✅ |
| Day 6 | 时间显示、本地持久化、Markdown 渲染 | ✅ |
| Day 7 | SQLite 数据库持久化（SQLAlchemy async） | ✅ |
| Day 8 | 依赖注入、中间件、WebSocket 实时通信 | ✅ |
| Day 10 | JWT 认证 & 多会话管理 | ✅ |
| Day 11 | 组件化重构（5 个组件）& 功能增强（置顶/搜索/导出） | ✅ |
| Day 14 | Docker 容器化部署（Dockerfile + docker-compose + Nginx） | ✅ |

### Month 2 · RAG 知识库

- [ ] LangChain + ChromaDB 向量检索
- [ ] 文档解析与嵌入

### Month 3 · Agent 智能体

- [ ] LangGraph + Function Calling
- [ ] 多工具调用

### Month 4 · 工程化 + 求职

- [ ] vLLM 推理服务 / MCP 协议
- [ ] 简历与项目打包

## 项目结构

```text
ai-fullstack-journey/
├── week1/
│   ├── backend/
│   │   ├── chat.py             ← Day 1: 非流式 CLI
│   │   ├── chat_stream.py      ← Day 2: 流式 CLI
│   │   ├── chat_managed.py     ← Day 3: 多轮对话 CLI
│   │   ├── database.py         ← Day 7: SQLAlchemy 异步模型
│   │   ├── main.py             ← Day 4-7: FastAPI（/chat /chat/stream /history）
│   │   └── requirements.txt
│   └── frontend/
│       └── src/
│           └── App.vue         ← Day 5-6: Vue3 聊天界面
├── week2/                      ← Week 2: 完整全栈项目
│   ├── backend/
│   │   ├── main.py             ← FastAPI + JWT + WebSocket
│   │   ├── database.py         ← SQLAlchemy 数据模型
│   │   ├── auth.py             ← 认证逻辑
│   │   └── dependencies.py     ← 依赖注入
│   ├── frontend/
│   │   └── src/
│   │       ├── components/     ← 5 个 Vue 组件
│   │       └── App.vue
│   ├── Dockerfile.backend      ← 后端容器化
│   ├── Dockerfile.frontend     ← 前端容器化
│   ├── docker-compose.yml      ← 服务编排
│   ├── nginx.conf              ← 反向代理配置
│   └── README.md               ← 详细项目文档
├── .gitignore
└── README.md
```

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3, TypeScript, Vite, Vitest, marked.js |
| 后端 | Python, FastAPI, Pydantic, SQLAlchemy, JWT, WebSocket, SSE |
| AI 模型 | DeepSeek API（openai 兼容格式） |
| 数据库 | SQLite + SQLAlchemy（async） + aiosqlite |
| 部署 | Docker, Docker Compose, Nginx |
| 规划中 | LangChain, LangGraph, ChromaDB, vLLM |

## 相关链接

- [我的掘金博客](https://juejin.cn/column/7666799391334973474)
