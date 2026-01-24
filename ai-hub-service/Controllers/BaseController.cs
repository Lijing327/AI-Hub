using Microsoft.AspNetCore.Mvc;

namespace ai_hub_service.Controllers;

/// <summary>
/// 基础控制器，提供租户ID获取方法
/// </summary>
[ApiController]
public abstract class BaseController : ControllerBase
{
    private const string TenantIdKey = "TenantId";

    /// <summary>
    /// 获取当前请求的租户ID
    /// </summary>
    /// <returns>租户ID，缺省返回 "default"</returns>
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
}
