# 1. 构建阶段：使用 Node.js 镜像编译前端代码
FROM node:20-alpine AS builder

WORKDIR /app

# 复制依赖文件并安装
COPY package*.json ./
RUN npm install

# 复制源码并构建
COPY . .
RUN npm run build

# 2. 运行阶段：使用 Nginx 镜像提供静态文件
FROM nginx:alpine

# 复制构建产物到 Nginx 的默认静态文件目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制自定义 Nginx 配置文件（可选，用于反向代理后端）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]