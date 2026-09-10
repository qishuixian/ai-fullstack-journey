# AI Fullstack Journey

从 10 年前端转型 AI 全栈工程师的学习记录。

## 在线体验

个人主页：[qishuixian.com](https://qishuixian.com/)，对应仓库入口文件 [index.html](./index.html)。

| 项目 | 在线地址 | 内容 |
| --- | --- | --- |
| Chat | [打开应用](https://qishuixian.com/chat/) | AI 流式对话 |
| Ask | [打开应用](https://qishuixian.com/ask/) | RAG 知识库与文档问答 |
| Week 11 · ReAct Studio | [打开应用](https://qishuixian.com/messageAgent/) | 实时工具调用、人工审核与会话历史 |

## 学习日志

### Month 1 · AI 聊天全栈应用

涉及目录：[week1](./week1)、[week2](./week2)、[week3](./week3)、[week4](./week4)。

- ✅ Vue 3 + TypeScript + Element Plus 前端搭建
- ✅ FastAPI + SQLAlchemy + JWT 后端开发
- ✅ DeepSeek API 流式对话集成
- ✅ Docker 多阶段构建（前端/后端镜像）
- ✅ Docker Compose 多服务编排
- ✅ Nginx 反向代理（路径路由 /chat/、/api/、/ws）
- ✅ 云服务器安全组与防火墙配置
- ✅ 域名解析与 ICP 备案流程
- ✅ 生产部署：本地构建 → tar 导出 → 服务器加载 → 容器启动

### Month 2 · RAG 知识库

涉及目录：[week5](./week5)。

- ✅ LangChain + ChromaDB 向量检索
- ✅ 文档解析与嵌入
- ✅ 用户登录注册与 JWT 认证
- ✅ PDF 文件上传、列表查看与删除
- ✅ 删除文件后同步移除 ChromaDB 向量
- ✅ Docker / Nginx / `/ask` 路径部署配置

### Month 3 · Agent 智能体

涉及目录：[week7](./week7)、[week8](./week8)、[week9](./week9)、[week10](./week10)、[week11](./week11)。

- ✅ LangChain 模型调用、Prompt、工具与 Agent 基础
- ✅ LangGraph `StateGraph`、节点、条件路由与消息状态
- ✅ Function Calling 与多工具调用
- ✅ 纯 Python 手写 ReAct 循环
- ✅ Supervisor / Worker 多 Agent 协作与并行分发
- ✅ SQLite Checkpoint 会话记忆持久化
- ✅ 重试、超时、最大迭代次数与循环熔断
- ✅ Agent 流式输出与流式工具调用消息合并
- ✅ Human-in-the-loop 敏感工具人工审核
- ✅ Python 原生 SQLite 对话记忆持久化
- ✅ 整合工具、审核、超时降级与会话管理的交互式 CLI Agent
- ✅ CLI Agent Web 化：FastAPI + SSE + Vue 3 + TypeScript + Element Plus
- ✅ 原生 EventSource、打字机回复、推理轮次与工具执行轨迹
- ✅ 浏览器人工审核弹窗、SQLite 会话隔离与历史恢复
- ✅ Week 11 Docker 双容器部署与 `/messageAgent/` 线上访问

#### Week 11 · ReAct Studio（已部署）

将 Week 10 Day 7 的手写 ReAct 循环改造成异步生成器，用 SSE 将模型公开回复、工具调用和审核请求实时推送到浏览器。支持工具超时降级、批准/拒绝、会话切换和刷新后恢复历史。

- 在线体验：[https://qishuixian.com/messageAgent/](https://qishuixian.com/messageAgent/)
- 项目说明：[Week 11 README](./week11/README.md)
- 开发端口：前端 `8003`、后端 `8083`
- 部署方式：Docker Compose + 前端 Nginx + 宿主机 HTTPS Nginx，SQLite 数据目录持久化
- 验证记录：镜像构建、子路径资源、真实模型 SSE、审核回传及容器重建后的历史恢复已验证；线上部署已由维护者确认完成

天气与邮件为教学模拟工具，邮件不会真实发送。详细运行命令、部署步骤和当前限制见项目 README。

### Month 4 · 工程化 + 求职

- [ ] vLLM 推理服务 / MCP 协议
- [ ] 简历与项目打包

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3, TypeScript, Vite, Vitest, marked.js |
| 后端 | Python, FastAPI, Pydantic, SQLAlchemy, JWT, WebSocket, SSE |
| AI / Agent | DeepSeek API（OpenAI 兼容格式）、LangChain、LangGraph、Function Calling、ReAct |
| 数据库 | SQLite + SQLAlchemy（async） + aiosqlite |
| 部署 | Docker, Docker Compose, Nginx, 腾讯云 |
| 规划中 | vLLM、MCP |

## 相关链接

- [我的掘金](https://juejin.cn/column/7666799391334973474)
- [我的个人博客](https://blog.csdn.net/qishuixian)


## 资料

- [ChatOpenAI 集成指南（LangChain 官方）](https://docs.langchain.com/oss/python/integrations/chat/openai)
- [ChatOpenAI API 参考](https://reference.langchain.com/python/langchain-openai/langchain_openai/chat_models/base/ChatOpenAI)
- [LangChain 中文文档（辅助参考）](https://langchain.cadn.net.cn/)
- [DeepSeek API 文档（中文）](https://api-docs.deepseek.com/zh-cn)

