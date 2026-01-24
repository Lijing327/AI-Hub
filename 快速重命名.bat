@echo off
chcp 65001 >nul
echo ========================================
echo 项目重命名工具
echo ========================================
echo.

if not exist "KnowledgeBase.API" (
    echo [错误] 未找到 KnowledgeBase.API 文件夹
    echo 请确保在项目根目录下运行此脚本
    pause
    exit /b 1
)

echo [1/2] 正在重命名文件夹: KnowledgeBase.API -^> ai-hub-service
ren "KnowledgeBase.API" "ai-hub-service" 2>nul
if errorlevel 1 (
    echo [错误] 文件夹重命名失败，可能文件夹正在被使用
    echo 请关闭 Visual Studio 或其他正在使用该文件夹的程序后重试
    pause
    exit /b 1
)
echo [成功] 文件夹重命名完成
echo.

if not exist "ai-hub-service\KnowledgeBase.API.csproj" (
    echo [警告] 未找到项目文件，可能已经重命名
) else (
    echo [2/2] 正在重命名项目文件: KnowledgeBase.API.csproj -^> ai-hub-service.csproj
    cd "ai-hub-service"
    ren "KnowledgeBase.API.csproj" "ai-hub-service.csproj" 2>nul
    if errorlevel 1 (
        echo [错误] 项目文件重命名失败
        cd ..
        pause
        exit /b 1
    )
    echo [成功] 项目文件重命名完成
    cd ..
)

echo.
echo ========================================
echo 重命名完成！
echo ========================================
echo.
echo 下一步操作：
echo 1. 在 Visual Studio 中重新加载项目
echo 2. 运行: dotnet clean
echo 3. 运行: dotnet restore
echo 4. 运行: dotnet build
echo.
pause
