# ============ 第一阶段：安装依赖 ============
FROM python:3.11-slim AS builder

WORKDIR /app

# 复制依赖文件并安装（使用国内镜像加速，可选）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============ 第二阶段：运行阶段 ============
FROM python:3.11-slim

WORKDIR /app

# 从 builder 阶段复制已安装的依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制项目代码（包含 main.py 及其他所有文件）
COPY . .

# 显式再次复制 main.py，确保它一定存在于容器中（防止 .dockerignore 或缓存干扰）
COPY ./main.py /app/main.py

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]