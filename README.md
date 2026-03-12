# 技能管理工具

一个用于管理和分发 AI 编程工具技能（skills）和智能体配置（Agent）的 Web 应用。

## ✨ 功能特点

- 🎯 **集中管理**：统一管理所有技能文件和智能体配置
- 🔄 **智能分发**：自动检测系统，选择最佳分发方式（软链接/拷贝）
- 🤖 **智能体中心**：专属 Agent 页面，管理工具的 AGENT.md 配置文件
- 🎨 **现代界面**：简约暗色系设计，卡片式布局，双页面切换
- 🛠️ **工具配置**：支持多个 AI 工具的技能和 Agent 配置
- 🧹 **清理功能**：自动清理失效链接和未使用文件
- 📋 **预览功能**：分发前预览所有操作

## 🚀 快速开始

### 1. 安装依赖

```bash
cd 技能管理工具/backend
pip install -r requirements.txt
```

### 2. 启动服务

**方式一：使用启动脚本（推荐）**
```bash
cd 技能管理工具
./start.sh
```

**方式二：手动启动**
```bash
cd 技能管理工具/backend
python app.py
```

### 3. 访问应用

- **Web 界面**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

## 📁 项目结构

```
技能管理工具/
├── backend/                    # 后端代码
│   ├── app.py                 # FastAPI 应用入口
│   ├── models.py              # 数据模型
│   ├── config_manager.py      # 配置管理
│   ├── skill_manager.py       # 技能管理
│   ├── agent_manager.py       # 智能体管理
│   ├── file_operations.py     # 文件操作
│   ├── api_routes.py          # API 路由
│   └── requirements.txt       # 依赖列表
├── frontend/                   # 前端代码
│   ├── index.html             # 主页面（包含技能和 Agent 两个页面）
│   ├── styles.css             # 样式文件
│   └── app.js                 # 交互逻辑
├── config/                     # 配置文件
│   └── config.json            # 全局配置
├── skills-library/             # 技能库目录
├── agent-library/              # 智能体库目录
│   └── AGENT.md               # 开发规范文档
├── docs/                       # 文档
│   ├── 开发计划.md
│   ├── 讨论要点.md
│   └── 核心决策清单.md
├── start.sh                    # 启动脚本
└── README.md                   # 本文件
```

## 🔧 配置说明

### 配置文件位置
`config/config.json`

### 配置示例
```json
{
  "master_skills_dir": "技能管理工具/skills-library",
  "tools": [
    {
      "id": "tool_001",
      "name": "OpenCode",
      "skills_dir": "~/.config/opencode/skills",
      "enabled": true,
      "distribute_method": "auto"
    }
  ]
}
```

### 分发方式说明

- **auto**（智能检测）：Mac/Linux 使用软链接，Windows 使用拷贝
- **symlink**（软链接）：节省空间，更新自动同步（需要权限）
- **copy**（拷贝）：独立文件，跨平台兼容

## 📡 API 接口

### 配置管理
- `GET /api/config` - 获取配置
- `POST /api/config` - 更新配置

### 工具管理
- `GET /api/tools` - 获取工具列表
- `POST /api/tools` - 添加工具
- `PUT /api/tools/{tool_id}` - 更新工具
- `DELETE /api/tools/{tool_id}` - 删除工具

### 技能管理
- `GET /api/skills` - 获取技能列表
- `GET /api/skills/{skill_id}` - 获取技能详情
- `GET /api/tools/{tool_id}/skills` - 获取工具已有技能列表
- `DELETE /api/tools/{tool_id}/skills/{skill_id}` - 删除工具下的技能

### 智能体管理
- `GET /api/agents` - 获取 Agent 库列表
- `GET /api/tools/{tool_id}/agent` - 获取工具的 Agent 配置
- `POST /api/tools/{tool_id}/agent` - 分发 Agent 文件到工具
- `DELETE /api/tools/{tool_id}/agent` - 删除工具的 Agent 配置

### 分发操作
- `POST /api/distribute` - 执行技能分发
- `POST /api/preview` - 预览分发操作
- `POST /api/cleanup` - 执行清理

详细 API 文档：http://localhost:8000/docs

## 🎨 界面预览

### 技能管理页面（SKILLS）
- **左侧工具列表**：显示已配置的工具，支持添加/删除工具
- **右侧技能库**：展示所有可用技能，支持搜索和多选
- **底部分发面板**：选择目标工具、分发方式、预览和执行分发

### 智能体中心页面（AGENT）
- **左侧工具列表**：显示工具的 Agent 配置状态
- **右侧 Agent 库**：展示所有可用的 Agent 文件
- **底部分发面板**：选择目标工具、分发 Agent 文件、选择分发方式

### 设计特点
- **暗色主题**：纯黑背景 + 琥珀金强调色
- **卡片布局**：工具列表 + 技能/Agent 库
- **响应式设计**：支持桌面和移动端
- **双页面切换**：顶部导航栏快速切换技能管理和智能体中心

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代化 Python Web 框架
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI 服务器
- **Python 3.8+** - 编程语言

### 前端
- **纯 HTML/CSS/JS** - 零依赖
- **Inter 字体** - 现代、清晰
- **Fetch API** - 数据交互
- **ES6+ 特性** - 现代 JavaScript

## 📖 使用指南

### 技能管理工作流

1. **添加工具**
   - 点击"添加工具"按钮
   - 填写工具名称、技能目录路径、Agent 文件路径（可选）
   - 选择分发方式（拷贝/软链接/智能检测）
   - 点击"添加"完成

2. **分发技能**
   - 在左侧工具列表中选择目标工具
   - 在右侧技能库中选择要分发的技能（支持多选）
   - 选择分发方式
   - 点击"预览"查看分发计划
   - 点击"执行分发"完成分发

3. **管理工具技能**
   - 点击工具卡片查看已有技能
   - 支持单个删除或批量删除技能
   - 删除操作会移除本地文件/软链接

### 智能体中心工作流

1. **查看 Agent 状态**
   - 切换到"智能体中心"页面
   - 左侧显示各工具的 Agent 配置状态
   - 右侧展示所有可用的 Agent 文件

2. **分发 Agent 文件**
   - 在左侧工具列表中选择目标工具
   - 在右侧 Agent 库中选择要分发的 Agent 文件
   - 选择分发方式
   - 点击"执行分发"完成分发

3. **删除 Agent 配置**
   - 选中工具后点击"删除选中"按钮
   - 确认删除操作

## 🔧 配置说明

### 配置文件位置
`config/config.json`

### 配置示例
```json
{
  "master_skills_dir": "技能管理工具/skills-library",
  "master_agent_dir": "技能管理工具/agent-library",
  "tools": [
    {
      "id": "tool_001",
      "name": "OpenCode",
      "skills_dir": "~/.config/opencode/skills",
      "agent_path": "~/.config/opencode/AGENT.md",
      "enabled": true,
      "distribute_method": "auto"
    }
  ]
}
```

### 分发方式说明

- **auto**（智能检测）：Mac/Linux 使用软链接，Windows 使用拷贝
- **symlink**（软链接）：节省空间，更新自动同步（需要权限）
- **copy**（拷贝）：独立文件，跨平台兼容
