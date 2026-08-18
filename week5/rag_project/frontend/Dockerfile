# 1. 构建阶段
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
COPY .env.production ./.env.production
RUN npm run build

# 2. 运行阶段
FROM nginx:alpine

# 直接把构建产物发布到 /ask/，和生产访问路径保持一致。
COPY --from=builder /app/dist /usr/share/nginx/html/ask/
COPY frontend-ask.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
