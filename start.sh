#!/bin/bash
# 技能管理工具启动脚本

echo "🚀 启动技能管理工具..."

# 检查是否在正确的目录
if [ ! -d "backend" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python 版本: $python_version"

# # 检查依赖
# echo "📦 检查依赖..."
cd backend

# if [ ! -d "venv" ]; then
#     echo "创建虚拟环境..."
#     python3 -m venv venv
# fi

# source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

# echo "安装依赖..."
# pip install -q -r requirements.txt

# 启动服务
echo ""
echo "✨ 启动 FastAPI 服务..."
echo "📍 访问地址: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python app.py
