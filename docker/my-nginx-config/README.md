# my-nginx-config

用 Nginx 作反向代理，将前端静态页面与 Node.js 后端整合到同一个 HTTP 入口的 Docker 练习项目。

## 项目结构

```
my-nginx-config/
├── default.conf          # Nginx 反向代理配置
├── html/
│   └── index.html        # 前端静态页面
└── my-backend/
    ├── dockerfile        # Node.js 后端镜像构建文件
    ├── package.json      # Node.js 项目描述
    └── server.js         # Express 后端服务（返回当前时间）
```

## 架构说明

```
浏览器
  │
  └─► Nginx (:80)
        ├── /          → 静态文件 (html/index.html)
        └── /api/*     → 反向代理到后端 (backend1:3001)
                            rewrite: /api/time → /time
```

- **Nginx** 负责统一入口：静态资源直接返回，`/api/*` 请求去掉 `/api` 前缀后转发给后端
- **后端** 是一个 Express 服务，监听 3001 端口，提供 `GET /time` 接口
- **前端** 页面调用 `/api/time` 拉取当前时间并展示

## 各文件说明

### `default.conf`

```nginx
upstream backend_servers {
    server backend1:3001;
    server backend2:3001;
    server backend3:3001;
}

server {
    listen 80;

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://backend1:3001;   # ← 当前直连 backend1
    }
}
```

> **注意**：`upstream backend_servers` 块已定义了 3 个后端实例，但 `proxy_pass` 目前指向 `backend1:3001` 而非 `http://backend_servers`，负载均衡未生效。改为 `proxy_pass http://backend_servers;` 即可启用轮询。

### `my-backend/dockerfile`

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json .
COPY server.js .
RUN npm install express
CMD ["node", "server.js"]
```

使用 Node 18 Alpine 最小镜像，构建时安装 Express，启动 `server.js`。

### `my-backend/server.js`

提供单一接口：

| 方法 | 路径    | 响应               |
|------|---------|-------------------|
| GET  | `/time` | 当前时间字符串     |

CORS 设置为 `*`（开发调试用）。

## 启动方式

本项目依赖容器名称 `backend1 / backend2 / backend3` 与 Nginx 容器互通，需通过 `docker-compose` 或自定义网络启动。示例 compose 结构：

```yaml
version: "3"
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./default.conf:/etc/nginx/conf.d/default.conf
      - ./html:/usr/share/nginx/html
    depends_on:
      - backend1

  backend1:
    build: ./my-backend
    networks:
      - app-net

networks:
  app-net:
```

启动：

```bash
docker compose up --build
```

访问 [http://localhost](http://localhost) 即可看到前端页面，页面自动调用 `/api/time` 显示当前时间。

## 已知问题 / 待改进

| 问题 | 描述 | 修复方式 |
|------|------|---------|
| 负载均衡未生效 | `proxy_pass` 指向单个容器而非 upstream 组 | 改为 `proxy_pass http://backend_servers;` |
| express 未写入依赖 | `package.json` 中无 express 声明 | `npm install express --save` 后重建镜像 |
| 缺少 docker-compose.yml | 无编排文件，手动启动容器繁琐 | 补充 compose 文件（参考上方示例）|
