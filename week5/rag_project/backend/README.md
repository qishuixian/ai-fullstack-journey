# Week 5 RAG Backend

`week5/rag_project/backend` 是基于 FastAPI 的 RAG 后端，负责用户注册登录、PDF 上传、向量入库、文件删除联动 ChromaDB、以及问答接口。

## 运行端口

- 本地/容器后端端口：`8001`
- Swagger 文档：`http://localhost:8001/docs`

## 主要能力

- JWT 注册与登录
- 用户级文件管理
- PDF 切分后写入 ChromaDB
- 删除文件时同步删除对应向量
- 提问时默认检索当前用户全部文件

## PDF 解析依赖

项目使用 `langchain_community.document_loaders.PyPDFLoader` 解析 PDF。
该加载器在当前版本下实际依赖 `pypdf`，因此 `requirements.txt` 中需要包含：

```text
pypdf==5.0.0
```

## 本地开发

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## 环境变量

在 `backend/.env` 中至少配置：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
SECRET_KEY=change-this-secret-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## Docker

`backend/Dockerfile` 会把服务暴露在容器 `8001` 端口。

上传文件目录固定为：

```text
/app/uploads
```

在 `docker-compose.prod.yml` 中，服务器目录 `./ask` 会挂载到这个目录：

```yaml
volumes:
  - ./ask:/app/uploads
```

这样服务器上的上传文件会统一落在部署目录下的 `ask/` 文件夹中。

## 数据目录

- SQLite：`/app/data/app.db`
- ChromaDB：`/app/chroma_db`
- 上传目录：`/app/uploads`
