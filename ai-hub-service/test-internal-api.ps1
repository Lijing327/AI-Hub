# 内部 API 测试脚本
# 需要先配置 appsettings.json 中的 InternalToken

$baseUrl = "http://localhost:5000"
$token = "your-internal-token-change-in-production"  # 替换为实际 Token
$tenantId = "default"

Write-Host "=== 测试 1: 批量创建知识条目 ===" -ForegroundColor Green

$batchCreateBody = @{
    articles = @(
        @{
            title = "YH-100 启动后无法进入自动模式"
            questionText = "【发生场景】待补充`n【具体表现】启动后无法进入自动模式`n【报警信息】无报警码`n【影响范围】待补充"
            causeText = "原因 1：安全门未完全关闭`n原因 2：液压站压力不足"
            solutionText = "步骤 1：检查安全门状态`n步骤 2：检查液压站压力表`n步骤 3：重新尝试切换"
            scopeJson = '{"设备型号": "YH-100"}'
            tags = "YH-100, 无报警码, 来源:测试"
            createdBy = "系统导入"
        },
        @{
            title = "YH-200 运行中压力波动大"
            questionText = "【发生场景】待补充`n【具体表现】运行中压力波动大`n【报警信息】E101`n【影响范围】待补充"
            causeText = "原因 1：压力传感器故障"
            solutionText = "步骤 1：更换压力传感器`n步骤 2：补充液压油"
            scopeJson = '{"设备型号": "YH-200"}'
            tags = "YH-200, E101, 来源:测试"
            createdBy = "系统导入"
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/ai/kb/articles/batch" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "X-Tenant-Id" = $tenantId
            "X-Internal-Token" = $token
        } `
        -Body $batchCreateBody

    Write-Host "批量创建成功！" -ForegroundColor Green
    Write-Host "成功数量: $($response.successCount)" -ForegroundColor Green
    Write-Host "失败数量: $($response.failureCount)" -ForegroundColor $(if ($response.failureCount -eq 0) { "Green" } else { "Yellow" })
    Write-Host "创建的 Article IDs: $($response.results | Where-Object { $_.success } | ForEach-Object { $_.articleId } | Join-String -Separator ', ')" -ForegroundColor Green
    
    $articleIds = $response.results | Where-Object { $_.success } | ForEach-Object { $_.articleId }
    
    if ($articleIds.Count -gt 0) {
        Write-Host "`n=== 测试 2: 批量发布知识条目 ===" -ForegroundColor Green
        
        $batchPublishBody = @{
            articleIds = $articleIds
        } | ConvertTo-Json

        $publishResponse = Invoke-RestMethod -Uri "$baseUrl/api/ai/kb/articles/publish/batch" `
            -Method POST `
            -Headers @{
                "Content-Type" = "application/json"
                "X-Tenant-Id" = $tenantId
                "X-Internal-Token" = $token
            } `
            -Body $batchPublishBody

        Write-Host "批量发布成功！" -ForegroundColor Green
        Write-Host "成功数量: $($publishResponse.successCount)" -ForegroundColor Green
        Write-Host "失败数量: $($publishResponse.failureCount)" -ForegroundColor $(if ($publishResponse.failureCount -eq 0) { "Green" } else { "Yellow" })
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
