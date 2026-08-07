# 1. 构建阶段
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 2. 运行阶段
FROM nginx:alpine

# 复制构建产物到子目录 /chat/
COPY --from=builder /app/dist /usr/share/nginx/html/chat/

# 复制自定义 Nginx 配置文件（注意文件名和路径）
# COPY frontend-chat.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]