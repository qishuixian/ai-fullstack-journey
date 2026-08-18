# Week 3 前端项目文档

## 📋 项目概述

基于 Vue 3 + TypeScript + Element Plus 构建的现代化 AI 聊天应用前端，提供完整的用户体验和交互功能。

## 🛠️ 技术栈

- **框架**: Vue 3.5.39 (Composition API + TypeScript)
- **UI 库**: Element Plus 2.9.3
- **状态管理**: Pinia 2.3.2
- **代码高亮**: Highlight.js 11.11.1
- **Markdown 渲染**: Marked 18.0.7 + marked-highlight 2.2.1
- **拖拽排序**: Sortable.js 1.15.6
- **构建工具**: Vite 8.1.1

## ✨ 核心功能

### 1. 用户认证
- ✅ 登录/注册表单（ElForm 组件）
- ✅ 表单验证（用户名 3-20 字符，密码 6-50 字符）
- ✅ JWT Token 存储和管理

### 2. 会话管理
- ✅ 创建/删除会话
- ✅ 会话列表拖拽排序
- ✅ 会话搜索/过滤
- ✅ 会话置顶功能
- ✅ 会话导出（JSON/Markdown/PDF）
- ✅ 右键菜单操作

### 3. 聊天功能
- ✅ 实时流式输出（SSE）
- ✅ Markdown 渲染
- ✅ 代码块语法高亮
- ✅ 代码复制按钮
- ✅ 消息编辑/删除
- ✅ 消息搜索
- ✅ 停止生成功能

### 4. 文件上传
- ✅ 支持多种文件类型
- ✅ 文件大小限制（10MB）
- ✅ 上传进度提示

### 5. 主题切换
- ✅ 浅色/深色主题
- ✅ Pinia Store 管理
- ✅ localStorage 持久化

## 🚀 快速开始

\`\`\`bash
npm install
npm run dev
\`\`\`

访问 `http://localhost:5173`

## 📦 核心依赖

- vue: ^3.5.39
- element-plus: ^2.9.3
- pinia: ^2.3.2
- highlight.js: ^11.11.1
- marked: ^18.0.7
- sortablejs: ^1.15.6

## 📁 项目结构

\`\`\`
frontend/
├── src/
│   ├── components/
│   │   ├── LoginForm.vue
│   │   ├── Sidebar.vue
│   │   ├── ChatArea.vue
│   │   ├── MessageList.vue
│   │   └── ChatInput.vue
│   ├── stores/
│   │   └── theme.ts
│   ├── styles/
│   │   └── global.css
│   └── main.ts
└── package.json
\`\`\`

## 👤 开发者

- 作者：戚水仙
- 时间：2026-07

## 📄 许可证

MIT License
