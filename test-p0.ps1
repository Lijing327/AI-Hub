# P0 测试脚本

Write-Host "=== P0 租户隔离测试 ===" -ForegroundColor Green

# 测试1: 不传 X-Tenant-Id，使用缺省 "default"
Write-Host "`n测试1: 不传 X-Tenant-Id，创建 article（应使用 default）" -ForegroundColor Yellow
$body1 = @{
    title = "Default Tenant Article"
    questionText = "Question"
    solutionText = "Solution"
} | ConvertTo-Json

try {
    $response1 = Invoke-RestMethod -Uri "http://localhost:5000/api/knowledgeitems" -Method POST -ContentType "application/json" -Body $body1
    Write-Host "✓ 创建成功" -ForegroundColor Green
    Write-Host "  ID: $($response1.id)" -ForegroundColor Cyan
    Write-Host "  TenantId: $($response1.tenantId)" -ForegroundColor Cyan
    $article1Id = $response1.id
} catch {
    Write-Host "✗ 创建失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 测试2: 传 X-Tenant-Id，使用指定租户
Write-Host "`n测试2: 传 X-Tenant-Id=tenant-a，创建 article" -ForegroundColor Yellow
$body2 = @{
    title = "Tenant A Article"
    questionText = "Question"
    solutionText = "Solution"
} | ConvertTo-Json

try {
    $headers2 = @{
        "X-Tenant-Id" = "tenant-a"
    }
    $response2 = Invoke-RestMethod -Uri "http://localhost:5000/api/knowledgeitems" -Method POST -ContentType "application/json" -Headers $headers2 -Body $body2
    Write-Host "✓ 创建成功" -ForegroundColor Green
    Write-Host "  ID: $($response2.id)" -ForegroundColor Cyan
    Write-Host "  TenantId: $($response2.tenantId)" -ForegroundColor Cyan
    $article2Id = $response2.id
} catch {
    Write-Host "✗ 创建失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 测试3: 不传 X-Tenant-Id 查询，应只返回 default 租户的数据
Write-Host "`n测试3: 不传 X-Tenant-Id 查询（应只返回 default 租户）" -ForegroundColor Yellow
try {
    $response3 = Invoke-RestMethod -Uri "http://localhost:5000/api/knowledgeitems/search" -Method GET
    Write-Host "✓ 查询成功" -ForegroundColor Green
    Write-Host "  返回记录数: $($response3.items.Count)" -ForegroundColor Cyan
    foreach ($item in $response3.items) {
        Write-Host "    - ID: $($item.id), Title: $($item.title), TenantId: $($item.tenantId)" -ForegroundColor Gray
    }
    $hasDefaultOnly = ($response3.items | Where-Object { $_.tenantId -eq "default" }).Count -eq $response3.items.Count
    if ($hasDefaultOnly) {
        Write-Host "  ✓ 所有记录都是 default 租户" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 存在非 default 租户的记录" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ 查询失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 测试4: 传 X-Tenant-Id=tenant-a 查询，应只返回 tenant-a 租户的数据
Write-Host "`n测试4: 传 X-Tenant-Id=tenant-a 查询（应只返回 tenant-a 租户）" -ForegroundColor Yellow
try {
    $headers4 = @{
        "X-Tenant-Id" = "tenant-a"
    }
    $response4 = Invoke-RestMethod -Uri "http://localhost:5000/api/knowledgeitems/search" -Method GET -Headers $headers4
    Write-Host "✓ 查询成功" -ForegroundColor Green
    Write-Host "  返回记录数: $($response4.items.Count)" -ForegroundColor Cyan
    foreach ($item in $response4.items) {
        Write-Host "    - ID: $($item.id), Title: $($item.title), TenantId: $($item.tenantId)" -ForegroundColor Gray
    }
    $hasTenantAOnly = ($response4.items | Where-Object { $_.tenantId -eq "tenant-a" }).Count -eq $response4.items.Count
    if ($hasTenantAOnly) {
        Write-Host "  ✓ 所有记录都是 tenant-a 租户" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 存在非 tenant-a 租户的记录" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ 查询失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 测试5: GetById 按 tenant_id 过滤
Write-Host "`n测试5: GetById 按 tenant_id 过滤" -ForegroundColor Yellow
Write-Host "  5.1: 缺省租户访问缺省租户的 article (ID=$article1Id)" -ForegroundColor Cyan
try {
    $response5a = Invoke-RestMethod -Uri "http://localhost:5000/api/knowledgeitems/$article1Id" -Method GET
    Write-Host "  ✓ 访问成功，TenantId: $($response5a.tenantId)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 访问失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "  5.2: 缺省租户访问 tenant-a 的 article (ID=$article2Id)" -ForegroundColor Cyan
try {
    $response5b = Invoke-RestMethod -Uri "http://localhost:5000/api/knowledgeitems/$article2Id" -Method GET
    Write-Host "  ✗ 应该返回404，但返回了数据" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "  ✓ 正确返回404（跨租户访问被阻止）" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 返回了其他错误: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "  5.3: tenant-a 访问自己的 article (ID=$article2Id)" -ForegroundColor Cyan
try {
    $headers5c = @{
        "X-Tenant-Id" = "tenant-a"
    }
    $response5c = Invoke-RestMethod -Uri "http://localhost:5000/api/knowledgeitems/$article2Id" -Method GET -Headers $headers5c
    Write-Host "  ✓ 访问成功，TenantId: $($response5c.tenantId)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 访问失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== 测试完成 ===" -ForegroundColor Green
