# Week 5 RAG Frontend

`week5/rag_project/frontend` 是 Vue 3 + TypeScript + Element Plus 构建的前端，部署目标路径为：

```text
https://qishuixian.com/ask
```

## 运行端口

- 本地 Vite 开发端口：`5173`
- Docker/Nginx 前端端口：`8081`

## 主要能力

- 登录/注册
- 文件管理列表
- 上传 PDF
- 全局上传 Loading
- 删除文件
- RAG 对话问答

## 本地开发

```bash
cd frontend
npm install
npm run dev
```

默认访问：

```text
http://localhost:5173
```

开发环境下通过 Vite 代理把 `/api` 转发到：

```text
http://127.0.0.1:8001
```

## 生产构建路径

生产环境静态资源基路径通过 `frontend/.env.production` 固定为：

```env
VITE_BASE_URL=/ask/
```

因此构建产物会以 `/ask/` 作为资源前缀，适配 `qishuixian.com/ask` 部署。

## Docker

`frontend/Dockerfile` 会：

1. 构建 Vue 前端
2. 将产物复制到容器内 `/usr/share/nginx/html/ask`
3. 使用 `frontend-ask.conf` 提供 `/ask/` 路径访问

容器对外端口为：

```text
8081
```
