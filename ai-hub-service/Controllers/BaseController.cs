using Microsoft.AspNetCore.Mvc;

namespace ai_hub_service.Controllers;

/// <summary>
/// 基础控制器，提供租户 ID 和用户 ID 获取方法
/// </summary>
[ApiController]
public abstract class BaseController : ControllerBase
{
    private const string TenantIdKey = "TenantId";

    /// <summary>
    /// 获取当前请求的租户 ID
    /// </summary>
    /// <returns>租户 ID，缺省返回 "default"</returns>
    protected string GetTenantId()
    {
        if (HttpContext.Items.TryGetValue(TenantIdKey, out var tenantIdObj) &&
            tenantIdObj is string tenantId &&
            !string.IsNullOrWhiteSpace(tenantId))
        {
            return tenantId;
        }

        // 如果中间件未设置，返回默认值（理论上不会发生，因为中间件总是会设置）
        return "default";
    }

    /// <summary>
    /// 获取当前用户的 ID
    /// </summary>
    /// <returns>用户 ID</returns>
    protected string GetUserId()
    {
        // 优先从 JWT claim 中获取
        var userId = User.FindFirst("user_id")?.Value;
        if (!string.IsNullOrWhiteSpace(userId))
            return userId;

        // 从请求头获取（用于测试或特殊场景）
        userId = HttpContext.Request.Headers["X-User-Id"].ToString();
        if (!string.IsNullOrWhiteSpace(userId))
            return userId;

        // 默认返回 anonymous
        return "anonymous";
    }
}
