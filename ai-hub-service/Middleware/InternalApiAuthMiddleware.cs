using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;

namespace ai_hub_service.Middleware;

/// <summary>
/// 内部 API 鉴权中间件
/// 验证 X-Internal-Token 请求头
/// </summary>
public class InternalApiAuthMiddleware
{
    private readonly RequestDelegate _next;
    private const string InternalTokenHeader = "X-Internal-Token";
    private readonly string _expectedToken;

    public InternalApiAuthMiddleware(RequestDelegate next, IConfiguration configuration)
    {
        _next = next;
        _expectedToken = configuration["InternalToken"] ?? throw new InvalidOperationException("InternalToken 配置项未设置");
    }

    public async Task InvokeAsync(HttpContext context)
    {
        // 只对 /api/ai/ 路径进行鉴权
        var path = context.Request.Path.Value?.ToLower() ?? "";
        if (path.StartsWith("/api/ai/"))
        {
            if (!context.Request.Headers.TryGetValue(InternalTokenHeader, out var tokenValue) ||
                string.IsNullOrWhiteSpace(tokenValue) ||
                tokenValue.ToString().Trim() != _expectedToken)
            {
                context.Response.StatusCode = 401;
                await context.Response.WriteAsync("Unauthorized: Invalid or missing X-Internal-Token");
                return;
            }
        }

        await _next(context);
    }
}
