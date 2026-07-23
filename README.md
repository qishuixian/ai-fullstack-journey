# AI Fullstack Journey 🚀

从 10 年前端转型 AI 全栈工程师的学习记录。

## 📅 学习日志

- [x] **Week 1 · Day 1**: Python 环境搭建 & DeepSeek API 非流式调用
- [x] **Week 1 · Day 2**: 流式输出（Streaming / SSE）
- [x] **Week 1 · Day 3**: 多轮对话上下文管理
- [ ] **Week 2**: FastAPI 后端搭建（`/chat` + `/chat/stream`）
- [ ] **Week 3**: Vue3 前端对接（流式渲染 + Markdown）
- [ ] **Week 4**: Docker 打包 & 云服务器部署
- [ ] **Month 2**: RAG 知识库（LangChain + ChromaDB）
- [ ] **Month 3**: Agent 智能体（LangGraph + Function Calling）
- [ ] **Month 4**: 工程化（vLLM / MCP）+ 求职准备

## 🗂️ 项目结构

```text
E:\my\ai-fullstack-journey\
├── .env                    ← 填入你的 DeepSeek Key
├── .env.example            ← Key 模板（参考用）
├── .gitignore              ← 保护 .env 不被提交
├── README.md               ← 项目说明（后续填博客链接）
├── week1\                  ← 第 1 周：CLI 聊天工具
│   ├── chat.py             ← Day 1: 非流式调用
│   ├── chat_stream.py      ← Day 2: 流式输出
│   └── chat_managed.py     ← Day 3: 对话管理
├── backend\                ← 第 2 周：FastAPI 后端
│   ├── main.py             ← FastAPI 入口
│   └── requirements.txt    ← Python 依赖清单
└── frontend\               ← 第 3 周：Vue3 前端
    ├── index.html
    ├── vite.config.ts
    └── src\
        ├── main.ts
        └── App.vue         ← 聊天界面
```

> 📌 当前状态：`week1/` 已完成 Day 1–3；`backend/`、`frontend/` 待创建。

## 🛠️ 技术栈

- **前端**: Vue 3, TypeScript, Pinia, Vite
- **后端**: Python, FastAPI, Pydantic
- **AI / 模型**: LangChain, LangGraph, RAG, Agent, DeepSeek
- **数据库**: ChromaDB, SQLite
- **工程化**: Docker, docker-compose, vLLM, MCP

## 🔗 相关链接

- [我的掘金博客](https://juejin.cn/user/xxx) <!-- 把你博客地址贴这里 -->
