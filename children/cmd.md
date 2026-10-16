# Children 上线命令手册

参考 `week11`，采用宿主机 Nginx + Docker 静态前端容器。无需后端、数据库或 API 密钥。

请求链路：`qishuixian.com/children/` → 宿主机 Nginx → `127.0.0.1:8004` → 容器 Nginx → Vue 页面。

## 1. 文件与前提

| 文件 | 用途 |
| --- | --- |
| `Dockerfile` | Node 22 构建，Nginx 提供 `dist` 静态文件 |
| `.dockerignore` | 排除本机依赖、构建目录、镜像归档和根目录原始图片 |
| `docker-compose.yml` | 从源码构建并启动 |
| `docker-compose.prod.yml` | 使用已经导入的镜像启动，不需要源码 |
| `nginx.container.conf` | 容器内完整站点配置，处理路由回退和静态资源缓存 |
| `nginx.children.conf` | 宿主机站点内引用的 location 片段 |

服务器需安装 Docker Engine、Docker Compose 2.17+ 和 Nginx。Windows 本机构建需启动 Docker Desktop，并使用 Linux containers。服务器需要能拉取基础镜像及 npm 依赖，或使用下面的“方式 B”上传本机构建的镜像。

默认端口 `8004` 只绑定宿主机回环地址，不必向公网开放。与 week11 的 `8003/8083` 不冲突。如果本地 Vite 占用 `8004`，先停止 Vite，或在 PowerShell 设置 `$env:CHILDREN_PORT = '18004'` 后测试；测试结束用 `Remove-Item Env:CHILDREN_PORT` 恢复。线上更改端口时，必须同步修改 `nginx.children.conf` 的上游端口。

`src/images/` 随源码进入构建阶段，只有通过 Vite 导入的素材才会进入最终 `dist`；当前欢迎页未引用这些图片。根目录的 `images/`（如有）被忽略。后续若使用 `public/` 发布素材，需要在 Dockerfile 中增加 `COPY public ./public`。

## 2. 方式 A：服务器从源码部署

以下是 Linux Bash 命令。先将项目的 `children` 目录上传至 `/opt/children`，目录内需包含 package 文件、源码、Dockerfile、两份 Nginx 配置和 Compose 文件。若使用 Git 拉取，进入实际的仓库 `children` 目录，并相应调整后文 include 路径。

```bash
cd /opt/children
docker version
docker compose version
docker compose config --quiet
docker compose build
docker compose up -d --no-build --wait
docker compose ps
docker compose exec frontend nginx -t
curl -f http://127.0.0.1:8004/children/
```

Dockerfile 会执行 `npm ci` 和 `npm run build`，服务器不需要额外安装 Node.js。继续执行第 4 节，配置域名入口。

## 3. 方式 B：Windows 构建镜像后上传（与 week11 相同）

### 本机 PowerShell

将 IP 和 SSH 用户替换为实际值。以下命令从仓库根目录开始：

```powershell
cd children
$DeployTarget = 'root@你的服务器IP'
docker version
docker compose config --quiet
docker buildx ls
docker compose build --builder default
# 每条命令成功后再执行下一条；构建失败不要导出旧镜像。
docker compose up -d --no-build --wait
docker compose exec frontend nginx -t
curl.exe -f http://127.0.0.1:8004/children/
docker save -o children-images.tar children-frontend:latest
ssh $DeployTarget 'mkdir -p /opt/children'
scp children-images.tar docker-compose.prod.yml nginx.children.conf "${DeployTarget}:/opt/children/"
```

`--builder default` 沿用 week11 的本机构建方式，以 `docker buildx ls` 的实际可用构建器为准。若发生证书、网络或镜像拉取错误，先处理 Docker 代理/DNS/镜像源问题，不要跳过构建继续部署。

镜像架构必须匹配服务器。服务器 `uname -m` 为 `x86_64` 对应 `linux/amd64`，`aarch64` 对应 `linux/arm64`。跨架构时，将上面的 compose build 命令替换为（按目标修改 platform）：

```powershell
docker buildx build --platform linux/amd64 --load -t children-frontend:latest .
```

### 服务器 Bash

```bash
cd /opt/children
docker load -i children-images.tar
docker compose -f docker-compose.prod.yml config --quiet
docker compose -f docker-compose.prod.yml up -d --wait
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml exec frontend nginx -t
curl -f http://127.0.0.1:8004/children/
```

镜像包含构建产物和容器 Nginx 配置，无需上传源码、`node_modules` 或 `dist`。本机测试完成后，可在本机 `children` 目录执行 `docker compose down`，不影响服务器。

## 4. 配置宿主机 Nginx

先找到当前生效的域名站点文件：

```bash
sudo nginx -T
```

找到 `server_name qishuixian.com;` 所属的 `server` 块和文件路径。保留现有首页、week11、证书等配置，不要覆盖整个站点或新建重复域名的 server。

将 `nginx.children.conf` 放到 `/opt/children/nginx.children.conf`，在已有站点 `server { ... }` 内添加：

```nginx
include /opt/children/nginx.children.conf;
```

该文件只有 location，不能直接放到 Nginx 的 http 顶层，也不要直接复制成 `/etc/nginx/conf.d/default.conf`。容器内使用的是另一份 `nginx.container.conf`。

如果已有前一版 README 中的 `/children` 静态托管 location，用这份 include 替换，不能重复定义同一路径。

- 站点提供 HTTP 时，在现有 80 端口站点中添加 include，入口为 `http://qishuixian.com/children`。
- 如果 HTTP 已统一跳转 HTTPS，在现有 443 站点内添加 include，保留 80 的跳转。HTTP 入口仍可访问，最终跳转到 `https://qishuixian.com/children/`。
- HTTP 和 HTTPS 各自提供内容时，在各自的 server 中引用一次。

代理配置关键点：`proxy_pass http://127.0.0.1:8004;` **末尾不加 `/`**，保留 `/children/` 路径。宿主机 `^~ /children/` 可避免现有静态文件正则拦截本项目 JS/CSS。

检查通过后重载：

```bash
sudo nginx -t && sudo systemctl reload nginx
```

宝塔环境请使用实际运行的 Nginx 检查并通过面板重载；非 systemd 环境可在检查通过后执行 `sudo nginx -s reload`。上述回环代理要求 Nginx 运行在宿主机，不能直接套用于另一个 Nginx 容器。

## 5. 上线验收

服务器执行：

```bash
# 无尾斜杠应返回 301，Location 为 /children/
curl -I http://127.0.0.1:8004/children
# 页面及子路由应返回 200，包括直接访问和刷新
curl -I http://127.0.0.1:8004/children/
curl -I http://127.0.0.1:8004/children/zhonwen
curl -I http://127.0.0.1:8004/children/yingwen
# 不存在的静态资源应返回 404，而不是首页 HTML
curl -I http://127.0.0.1:8004/children/assets/missing.js
# 域名入口，可跟随 HTTP → HTTPS 跳转
curl -IL http://qishuixian.com/children
curl -IL http://qishuixian.com/children/zhonwen
curl -IL http://qishuixian.com/children/yingwen
```

浏览器检查首页两个按钮、中文/英文页直接刷新、返回首页和前进后退；手机检查卡片单列、文字不溢出、按钮可点击。开发者工具中实际 JS/CSS 应来自 `/children/assets/` 且返回 200；`index.html` 使用 `no-cache`，带哈希的资源长期缓存。

## 6. 更新、日志、停止与回滚

源码方式更新：将最新源码同步至部署目录，然后执行：

```bash
cd /opt/children
docker compose build
docker compose up -d --no-build --wait
docker compose logs --tail=100 frontend
```

镜像方式更新：本机重新 build、save、scp；服务器重新 load，然后执行：

```bash
cd /opt/children
docker compose -f docker-compose.prod.yml up -d --wait
docker compose -f docker-compose.prod.yml logs --tail=100 frontend
```

仅修改宿主机 `nginx.children.conf` 时，执行宿主机 `nginx -t` 后重载即可；修改容器配置、源码或依赖都需要重新构建镜像并重建容器。不要仅执行 restart 期待替换镜像。

需要回滚保障时，在服务器加载/构建新镜像**之前**，先记录旧镜像（首次部署跳过）：

```bash
cd /opt/children
docker image tag children-frontend:latest children-frontend:rollback
```

新版本异常时，使用统一的镜像版 Compose 回滚：

```bash
CHILDREN_IMAGE_TAG=rollback docker compose -f docker-compose.prod.yml up -d --wait
```

此回滚标签只保留最近一次手动标记的版本；正式使用可将 tag 换成日期或发布版本号。回滚后再次执行默认 up 会切回 latest，需要先修复或明确选择版本。

停止镜像部署：

```bash
docker compose -f docker-compose.prod.yml down
```

源码方式省略 `-f docker-compose.prod.yml`。停止期间域名会返回 502，恢复用对应的 up 命令。

## 7. 常见问题

| 现象 | 检查 |
| --- | --- |
| 无法连接 Docker API | 启动 Docker Desktop / 服务器 Docker 服务，确认使用 Linux 引擎 |
| 8004 被占用 | 停止本机 Vite 或设置 CHILDREN_PORT；线上同步调整代理端口 |
| 域名返回 502 | 检查 compose ps、日志及 `curl http://127.0.0.1:8004/children/` |
| 容器正常，域名 404 | 检查生效的 HTTP/HTTPS server、include 位置及 Nginx 是否重载 |
| 子页刷新 404 | 确认镜像使用 nginx.container.conf 的 History 回退 |
| 页面空白或资源 404 | 检查资源前缀 `/children/`，以及 proxy_pass 是否误加尾斜杠 |
| 新页面未生效 | 确认重新构建并执行 up；检查是否仍在运行 rollback tag |

## 8. 本次验证记录（2026-10-16）

- 两份 Compose 配置检查通过，两份 Nginx 配置通过真实 Nginx 语法检查（宿主机片段在独立 server 中验证）。
- 重新生成完整的 package-lock.json；Linux 镜像内 `npm ci`、TypeScript 检查、Vite 生产构建成功，生成 `children-frontend:latest`。
- 镜像版 Compose 实际启动成功，容器健康检查为 healthy。
- 首页、中文/英文子路由及实际 JS/CSS 返回 200；入口重定向为 301，缺失静态资源返回 404；HTML 与哈希资源缓存头符合配置。
- 本地验证临时使用 18004 避开开发服务，测试容器已清理。正式部署配置默认端口始终为 **8004**。

尚未连接线上服务器或修改线上 Nginx，域名实际验收需在部署后执行。上述检查不代替手机浏览器的视觉和交互验收。
