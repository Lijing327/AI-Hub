using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;

namespace ai_hub_service.Middleware;

/// <summary>
/// 租户隔离中间件
/// 从请求头 X-Tenant-Id 读取租户ID，并存入 HttpContext.Items
/// 缺省租户：测试环境(ai_hub_test)用 default_test，生产用 default
/// </summary>
public class TenantMiddleware
{
    private readonly RequestDelegate _next;
    private readonly string _defaultTenant;
    private const string TenantIdHeader = "X-Tenant-Id";
    private const string TenantIdKey = "TenantId";

    public TenantMiddleware(RequestDelegate next, IConfiguration configuration)
    {
        _next = next;
        // 测试环境(ai_hub_test)默认 default_test，生产默认 default；可通过 appsettings 覆盖
        _defaultTenant = configuration["Tenant:DefaultTenant"] ?? "default";
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

        // 从请求头读取 X-Tenant-Id，缺省使用配置的默认租户
        string tenantId = _defaultTenant;
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
