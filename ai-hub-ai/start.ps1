# Python 服务启动脚本
# 使用 uvicorn 启动服务（推荐方式）

Write-Host "启动 AI Hub Excel 导入服务..." -ForegroundColor Green

# 检查虚拟环境
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "错误: 虚拟环境不存在，请先创建虚拟环境" -ForegroundColor Red
    exit 1
}

# 检查 .env 文件
if (-not (Test-Path ".env")) {
    Write-Host "警告: .env 文件不存在，将使用默认配置" -ForegroundColor Yellow
    Write-Host "建议: 复制 .env.example 为 .env 并配置" -ForegroundColor Yellow
}

# 启动服务
.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
