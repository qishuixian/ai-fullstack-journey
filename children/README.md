# 语言小乐园

参考 `week11/frontend`，使用 Vue 3 + TypeScript + Vite + Element Plus，增加 Vue Router 的 History 路由。项目直接放在 `children`，图片素材位于 `src/images`。

## 本地运行

需要 Node.js >= 20.19.0。

```sh
npm install
npm run dev
```

打开 http://localhost:8004/children/ 。

## 页面

- `/children` 或 `/children/`：首页，提供“进入中文”和“进入英文”按钮。
- `/children/zhonwen`：中文识字页，路径按需求中的 `zhonwen` 拼写保留。使用 Element Plus 按钮、下拉框和图片组件，默认字体模式；16 页，每页四个字，支持图片/字体切换和上一页、下一页。
- `/children/yingwen`：英文欢迎页。

内页支持返回首页及浏览器前进后退，英文页保留欢迎页。首页在移动端使用单列入口卡片，中文页使用两列识字卡片；图片由 `src/images` 按字匹配，居中等比完整显示，第14页按要求保留两个“雪”。页面包含 viewport 与安全区适配。

## 构建和部署

推荐按 [上线命令手册 cmd.md](./cmd.md) 使用与 week11 相同的 Docker + 宿主机 Nginx 方案，包含源码构建、镜像上传、域名配置、验证和回滚。

```sh
docker compose build
docker compose up -d --no-build --wait
```

容器监听 `127.0.0.1:8004`，请先停止同端口的 Vite 开发服务。`nginx.container.conf` 用于容器内，`nginx.children.conf` 用于宿主机已有站点。

### 可选：不使用 Docker 的静态部署

下面的静态部署与 Docker 代理方案二选一，不要在宿主机同时配置两套 `/children/` location。

```sh
npm run build
npm run preview
```

将 `dist` 内的文件复制到网站根目录下的 `children/` 文件夹，例如 `/var/www/qishuixian/children/`。Vite 的资源前缀已设置为 `/children/`。

在现有 Nginx 网站的 server 中配置（root 替换成实际网站根目录）：

```nginx
root /var/www/qishuixian;

location = /children {
    return 301 /children/;
}

location /children/ {
    try_files $uri $uri/ /children/index.html;
}
```
文件上传到位后执行：
sudo nginx -t && sudo systemctl reload nginx
History 路由必须回退到 `/children/index.html`，否则直接访问或刷新中文、英文页面会返回 404。本地创建和构建不会自动发布到 qishuixian.com。
