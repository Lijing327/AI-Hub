#!/bin/bash
# Python 服务启动脚本
# 使用 uvicorn 启动服务（推荐方式）

echo "启动 AI Hub Excel 导入服务..."

# 检查虚拟环境
if [ ! -f ".venv/bin/python" ]; then
    echo "错误: 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "警告: .env 文件不存在，将使用默认配置"
    echo "建议: 复制 .env.example 为 .env 并配置"
fi

# 启动服务
.venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
