# Python 服务 Excel 导入测试脚本（PowerShell）

$baseUrl = "http://localhost:8000"
$excelFile = "test.xlsx"  # 替换为实际的 Excel 文件路径

Write-Host "=== 测试 Excel 导入 ===" -ForegroundColor Green

if (-not (Test-Path $excelFile)) {
    Write-Host "错误: Excel 文件不存在: $excelFile" -ForegroundColor Red
    Write-Host "请创建一个测试 Excel 文件，包含以下列：" -ForegroundColor Yellow
    Write-Host "  设备型号 | 故障现象 | 报警信息 | 原因分析 | 处理方法" -ForegroundColor Yellow
    exit 1
}

try {
    # 使用 multipart/form-data 上传文件
    $form = @{
        file = Get-Item $excelFile
    }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/import/excel" `
        -Method POST `
        -Form $form `
        -ContentType "multipart/form-data"
    
    Write-Host "导入成功！" -ForegroundColor Green
    Write-Host "总行数: $($response.total_rows)" -ForegroundColor Cyan
    Write-Host "成功数量: $($response.success_count)" -ForegroundColor Green
    Write-Host "失败数量: $($response.failure_count)" -ForegroundColor $(if ($response.failure_count -eq 0) { "Green" } else { "Yellow" })
    Write-Host "创建的 Article IDs: $($response.article_ids -join ', ')" -ForegroundColor Green
    
    if ($response.failures.Count -gt 0) {
        Write-Host "`n失败详情:" -ForegroundColor Yellow
        $response.failures | ForEach-Object {
            Write-Host "  行 $($_.row_index): $($_.reason)" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "错误: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "响应内容: $responseBody" -ForegroundColor Red
    }
}

Write-Host "`n测试完成！" -ForegroundColor Cyan
