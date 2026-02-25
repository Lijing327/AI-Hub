using Microsoft.AspNetCore.Http;
using AiHub.Utils;
using System.Security.Claims;
using Microsoft.Extensions.Hosting;

namespace AiHub.Middleware
{
    public class JwtMiddleware
    {
        private readonly RequestDelegate _next;
        private readonly JwtUtils _jwtUtils;

        public JwtMiddleware(RequestDelegate next, JwtUtils jwtUtils)
        {
            _next = next;
            _jwtUtils = jwtUtils;
        }

        public async Task InvokeAsync(HttpContext context)
        {
            // 获取Authorization头
            var authHeader = context.Request.Headers["Authorization"].FirstOrDefault();

            if (authHeader != null && authHeader.StartsWith("Bearer "))
            {
                var token = authHeader.Substring("Bearer ".Length).Trim();

                if (token != null)
                {
                    // 验证token
                    var principal = _jwtUtils.ValidateToken(token);

                    if (principal != null)
                    {
                        // 将用户信息添加到上下文
                        context.User = principal;
                    }
                }
            }

            // 继续管道
            await _next(context);
        }
    }

    public static class JwtMiddlewareExtensions
    {
        public static IApplicationBuilder UseJwtMiddleware(this IApplicationBuilder builder)
        {
            return builder.UseMiddleware<JwtMiddleware>();
        }

        public static WebApplication UseJwtMiddleware(this WebApplication app)
        {
            app.UseMiddleware<JwtMiddleware>();
            return app;
        }
    }
}