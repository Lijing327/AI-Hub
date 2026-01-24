using Microsoft.AspNetCore.Http;

namespace ai_hub_service.Middleware;

/// <summary>
/// 租户隔离中间件
/// 从请求头 X-Tenant-Id 读取租户ID，并存入 HttpContext.Items
/// </summary>
public class TenantMiddleware
{
    private readonly RequestDelegate _next;
    private const string TenantIdHeader = "X-Tenant-Id";
    private const string TenantIdKey = "TenantId";

    public TenantMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        // 跳过 Swagger 和静态文件请求
        var path = context.Request.Path.Value?.ToLower() ?? "";
        if (path.StartsWith("/swagger") || path.StartsWith("/uploads"))
        {
            await _next(context);
            return;
        }

        // 从请求头读取 X-Tenant-Id，缺省使用 "default"
        string tenantId = "default";
        if (context.Request.Headers.TryGetValue(TenantIdHeader, out var tenantIdValue) &&
            !string.IsNullOrWhiteSpace(tenantIdValue))
        {
            var headerValue = tenantIdValue.ToString().Trim();
            if (!string.IsNullOrEmpty(headerValue))
            {
                tenantId = headerValue;
            }
        }

        // 存入 HttpContext.Items
        context.Items[TenantIdKey] = tenantId;

        await _next(context);
    }
}
