# PowerShell 脚本：重命名项目文件夹和项目文件
# 使用方法：在项目根目录下运行此脚本

Write-Host "开始重命名项目..." -ForegroundColor Green

# 1. 重命名项目文件夹
if (Test-Path "KnowledgeBase.API") {
    Write-Host "重命名文件夹: KnowledgeBase.API -> ai-hub-service" -ForegroundColor Yellow
    Rename-Item -Path "KnowledgeBase.API" -NewName "ai-hub-service" -Force
    Write-Host "✓ 文件夹重命名完成" -ForegroundColor Green
} else {
    Write-Host "✗ 未找到 KnowledgeBase.API 文件夹" -ForegroundColor Red
    exit 1
}

# 2. 重命名项目文件
$projectFile = "ai-hub-service\KnowledgeBase.API.csproj"
if (Test-Path $projectFile) {
    Write-Host "重命名项目文件: KnowledgeBase.API.csproj -> ai-hub-service.csproj" -ForegroundColor Yellow
    Rename-Item -Path $projectFile -NewName "ai-hub-service.csproj" -Force
    Write-Host "✓ 项目文件重命名完成" -ForegroundColor Green
} else {
    Write-Host "✗ 未找到项目文件" -ForegroundColor Red
}

Write-Host "`n重命名完成！" -ForegroundColor Green
Write-Host "下一步：运行 'dotnet clean' 和 'dotnet restore' 清理并重新构建项目" -ForegroundColor Cyan
