# 第一阶段：构建
FROM node:20-alpine AS builder

WORKDIR /app

# 复制依赖文件并安装
COPY package*.json ./
RUN npm install

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# 第二阶段：运行
FROM nginx:alpine

# 复制构建产物到 nginx 目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露 80 端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]