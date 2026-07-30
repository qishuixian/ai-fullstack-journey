# Week 3 - AI 聊天应用进阶版

基于 Week2 的基础上，使用 **Element Plus** UI 框架重构界面，增强用户体验和交互功能。

## 📋 项目概述

本周目标是将 Week2 的基础聊天应用升级为功能完善、体验优秀的企业级应用。

## 🛠️ 技术栈

### 前端
- **框架**: Vue 3 + TypeScript
- **UI 库**: Element Plus 2.9.3
- **状态管理**: Pinia 2.3.2
- **代码高亮**: Highlight.js 11.11.1
- **Markdown**: Marked 18.0.7 + marked-highlight 2.2.1
- **拖拽排序**: Sortable.js 1.15.6
- **构建工具**: Vite 8.1.1

### 后端
- **框架**: FastAPI 0.139.2
- **数据库**: SQLite + SQLAlchemy 2.0.51 + aiosqlite 0.22.1
- **认证**: JWT (python-jose 3.5.0)
- **AI 接口**: DeepSeek API (openai 2.48.0)
- **文件处理**: aiofiles 25.1.0

## ✨ 功能实现进度

### ✅ Day 1: UI 框架选型与集成
- 引入 Element Plus 组件库
- 配置全局样式和主题 CSS 变量
- 注册 Element Plus 图标库

**核心文件**:
- [frontend/src/main.ts](frontend/src/main.ts) - 全局配置
- [frontend/src/styles/global.css](frontend/src/styles/global.css) - 全局样式

### ✅ Day 2: 登录/注册页改造
- 使用 ElForm + ElInput 重写登录表单
- 添加表单校验规则（用户名 3-20 字符，密码 6-50 字符）
- ElMessage 消息提示优化
- 图标前缀增强视觉体验

**核心组件**:
- [frontend/src/components/LoginForm.vue](frontend/src/components/LoginForm.vue)

### ✅ Day 3: 会话侧边栏增强
- 拖拽排序（Sortable.js）
- 右键菜单/下拉菜单（ElDropdown）
- 空状态提示（ElEmpty）
- 搜索功能优化
- 置顶会话（星标图标）

**核心组件**:
- [frontend/src/components/Sidebar.vue](frontend/src/components/Sidebar.vue)

**功能特性**:
- 拖拽排序会话（搜索时自动禁用）
- 右键菜单：置顶、重命名、导出、删除
- 导出格式：JSON / Markdown / PDF

### ✅ Day 4: 聊天区体验升级
- 代码块语法高亮（Highlight.js + GitHub Dark 主题）
- 代码复制按钮（点击后 2 秒恢复）
- Loading 动画（ElIcon 旋转）
- Marked + marked-highlight 集成
- 消息气泡优化

**核心组件**:
- [frontend/src/components/MessageList.vue](frontend/src/components/MessageList.vue)
- [frontend/src/components/ChatArea.vue](frontend/src/components/ChatArea.vue)

### ✅ Day 5: 主题切换（浅色/深色）
- Pinia Store 管理主题状态
- CSS 变量实现主题切换
- localStorage 持久化主题
- 根元素动态添加 `.dark` 类
- 主题切换按钮（日/月图标）

**核心文件**:
- [frontend/src/stores/theme.ts](frontend/src/stores/theme.ts) - 主题状态管理
- [frontend/src/styles/global.css](frontend/src/styles/global.css) - CSS 变量定义

### ✅ Day 6: 消息编辑/删除 + 文件上传
#### 后端功能
- 消息编辑接口：`PATCH /messages/{message_id}`
- 消息删除接口：`DELETE /messages/{message_id}`
- 文件上传接口：`POST /upload`（限制 10MB，类型白名单）
- 文件下载接口：`GET /uploads/{filename}`

#### 前端功能
- 消息编辑 UI（鼠标悬停显示编辑按钮）
- 消息删除 UI（确认对话框）
- 文件上传 UI（ElUpload + 回形针图标）
- 消息搜索功能（🔍按钮切换搜索栏）
- 实时搜索过滤消息内容

**安全措施**:
- 文件类型白名单验证
- 文件大小限制（10MB）
- UUID 唯一文件名防冲突

### ✅ Day 7+: 额外功能增强
- **会话拖拽排序持久化**（保存到后端）
- **PDF 导出功能**（侧边栏菜单项）
- **修复双 AI 消息 bug**（流式输出优化）
- **完整的项目文档**

## 📁 项目结构

```
week3/
├── backend/
│   ├── main.py              # FastAPI 主应用
│   ├── auth.py              # JWT 认证逻辑
│   ├── database.py          # SQLAlchemy 数据库模型
│   ├── dependencies.py      # 依赖注入
│   ├── requirements.txt     # Python 依赖
│   ├── .env                 # 环境变量（需自行创建）
│   └── uploads/             # 上传文件目录
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LoginForm.vue      # 登录/注册组件
│   │   │   ├── Sidebar.vue        # 侧边栏组件
│   │   │   ├── ChatArea.vue       # 聊天主区域
│   │   │   ├── MessageList.vue    # 消息列表
│   │   │   └── ChatInput.vue      # 输入框组件
│   │   ├── stores/
│   │   │   └── theme.ts           # 主题状态管理
│   │   ├── styles/
│   │   │   └── global.css         # 全局样式
│   │   ├── App.vue                # 根组件
│   │   └── main.ts                # 入口文件
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md              # 前端开发文档
│
└── README.md                  # 本文件
```

## 🚀 快速开始

### 前置要求
- Python 3.10+
- Node.js 18+
- npm 或 pnpm

### 后端设置

```bash
cd week3/backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 配置 .env 文件
echo "DEEPSEEK_API_KEY=your_api_key_here" > .env

# 运行后端
uvicorn main:app --reload
```

后端服务：`http://127.0.0.1:8000`

### 前端设置

```bash
cd week3/frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

前端服务：`http://localhost:5173`

### Docker 容器化部署

```bash
# 构建并启动所有服务
docker compose up --build -d

# 查看日志
docker compose logs -f

# 查看容器状态
docker compose ps

# 重启服务
docker compose restart

# 停止并移除容器（数据卷保留）
docker compose down
```

## 📦 核心依赖版本

### 前端
```json
{
  "vue": "^3.5.39",
  "element-plus": "^2.9.3",
  "@element-plus/icons-vue": "^2.3.1",
  "pinia": "^2.3.2",
  "highlight.js": "^11.11.1",
  "marked": "^18.0.7",
  "marked-highlight": "^2.2.1",
  "sortablejs": "^1.15.6"
}
```

### 后端
```txt
fastapi==0.139.2
sqlalchemy==2.0.51
aiofiles==25.1.0
python-jose[cryptography]==3.5.0
openai==2.48.0
```

## 🎯 相比 Week2 的改进

| 功能 | Week2 | Week3 |
|------|-------|-------|
| UI 框架 | 原生 HTML/CSS | Element Plus |
| 状态管理 | 无 | Pinia |
| 代码高亮 | 无 | Highlight.js |
| 拖拽排序 | 无 | Sortable.js ✅ |
| 主题切换 | 无 | 浅色/深色 ✅ |
| 文件上传 | 无 | 支持 ✅ |
| 消息管理 | 无 | 编辑/删除 ✅ |
| 消息搜索 | 无 | 实时搜索 ✅ |
| PDF 导出 | 无 | 支持 ✅ |
| 响应式设计 | 部分 | 完整 ✅ |

## 🔮 未来优化方向

- [ ] 移动端手势支持（左滑删除等）
- [ ] 虚拟滚动优化长列表性能
- [ ] 多语言支持（i18n）
- [ ] PWA 支持（离线访问）
- [ ] 语音输入功能
- [ ] 消息引用/回复
- [ ] 代码块主题切换
- [ ] 会话分组管理

## 💡 学习要点

1. **Element Plus 集成**: 如何在 Vue 3 项目中集成和配置 UI 库
2. **Pinia 状态管理**: Store 的创建、使用和持久化
3. **CSS 变量主题**: 使用 CSS 自定义属性实现主题切换
4. **代码高亮**: Highlight.js + Marked 的集成方案
5. **拖拽排序**: Sortable.js 的基本使用和事件处理
6. **文件上传**: FastAPI 文件上传处理和安全策略
7. **响应式设计**: CSS Media Queries + 移动端适配
8. **TypeScript**: Vue 3 + TypeScript 最佳实践

## ❓ 常见问题

### 1. Element Plus 样式不生效？
确保在 `main.ts` 中导入了 `element-plus/dist/index.css`

### 2. 代码高亮显示异常？
检查是否导入了 highlight.js 的 CSS 主题文件：
```ts
import 'highlight.js/styles/github-dark.css'
```

### 3. 主题切换不持久化？
确认 `theme.ts` 中的 `watch` 已正确设置 `immediate: true`

### 4. 文件上传失败？
检查：
- 后端 `uploads/` 目录是否存在且有写入权限
- 文件大小是否超过 10MB
- 文件类型是否在白名单中

### 5. requirements.txt 编码错误？
使用提供的 ASCII 编码版本，或重新生成：
```bash
pip freeze > requirements.txt
```

## 📖 API 接口文档

### 认证接口
- `POST /register` - 用户注册
- `POST /token` - 用户登录

### 会话接口
- `GET /sessions` - 获取会话列表
- `POST /sessions` - 创建新会话
- `PATCH /sessions/{id}` - 更新会话名称
- `PATCH /sessions/{id}/pin` - 置顶/取消置顶
- `DELETE /sessions/{id}` - 删除会话
- `GET /sessions/{id}/export?format={json|markdown}` - 导出会话

### 聊天接口
- `POST /chat` - 非流式聊天
- `POST /chat/stream` - 流式聊天（SSE）
- `GET /history?session_id={id}` - 获取历史记录

### 消息接口（新增）
- `PATCH /messages/{id}` - 编辑消息
- `DELETE /messages/{id}` - 删除消息

### 文件接口（新增）
- `POST /upload` - 上传文件
- `GET /uploads/{filename}` - 下载文件

### WebSocket
- `ws://localhost:8000/ws?token={token}` - 实时通信

## 👤 作者

- 开发者：戚水仙
- 时间：2026-07
- 项目：AI 全栈学习之旅 - Week 3

## 📄 许可证

MIT License
