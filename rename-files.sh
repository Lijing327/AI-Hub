#!/bin/bash
# Bash 脚本：重命名项目文件夹和项目文件
# 使用方法：在项目根目录下运行此脚本

echo "开始重命名项目..."

# 1. 重命名项目文件夹
if [ -d "KnowledgeBase.API" ]; then
    echo "重命名文件夹: KnowledgeBase.API -> ai-hub-service"
    mv "KnowledgeBase.API" "ai-hub-service"
    echo "✓ 文件夹重命名完成"
else
    echo "✗ 未找到 KnowledgeBase.API 文件夹"
    exit 1
fi

# 2. 重命名项目文件
if [ -f "ai-hub-service/KnowledgeBase.API.csproj" ]; then
    echo "重命名项目文件: KnowledgeBase.API.csproj -> ai-hub-service.csproj"
    mv "ai-hub-service/KnowledgeBase.API.csproj" "ai-hub-service/ai-hub-service.csproj"
    echo "✓ 项目文件重命名完成"
else
    echo "✗ 未找到项目文件"
fi

echo ""
echo "重命名完成！"
echo "下一步：运行 'dotnet clean' 和 'dotnet restore' 清理并重新构建项目"
