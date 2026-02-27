using ai_hub_service.DTOs;
using AiHub.DTOs;
using AiHub.Models;

namespace AiHub.Services;

/// <summary>
/// 工单服务接口
/// </summary>
public interface ITicketService
{
    /// <summary>
    /// 创建工单
    /// </summary>
    Task<TicketDetailDto> CreateAsync(CreateTicketRequest request, string userId, string tenantId);

    /// <summary>
    /// 获取工单列表（支持分页和筛选）
    /// </summary>
    Task<PagedResultDto<TicketListDto>> ListAsync(TicketQueryRequest query, string userId, string tenantId, bool isStaff);

    /// <summary>
    /// 获取工单详情
    /// </summary>
    Task<TicketDetailDto?> GetByIdAsync(Guid ticketId, string userId, string tenantId, bool isStaff);

    /// <summary>
    /// 更新工单
    /// </summary>
    Task<TicketDetailDto?> UpdateAsync(Guid ticketId, UpdateTicketRequest request, string userId, string tenantId);

    /// <summary>
    /// 开始处理工单
    /// </summary>
    Task<TicketDetailDto?> StartAsync(Guid ticketId, StartTicketRequest? request, string userId, string tenantId);

    /// <summary>
    /// 标记工单已解决
    /// </summary>
    Task<TicketDetailDto?> ResolveAsync(Guid ticketId, ResolveTicketRequest request, string userId, string tenantId);

    /// <summary>
    /// 关闭工单
    /// </summary>
    Task<TicketDetailDto?> CloseAsync(Guid ticketId, CloseTicketRequest? request, string userId, string tenantId);

    /// <summary>
    /// 添加工单日志/备注
    /// </summary>
    Task<TicketLogDto> AddLogAsync(Guid ticketId, CreateTicketLogRequest request, string userId, string tenantId);

    /// <summary>
    /// 获取工单日志列表
    /// </summary>
    Task<List<TicketLogDto>> GetLogsAsync(Guid ticketId, string userId, string tenantId);

    /// <summary>
    /// 将工单转换为知识库文章
    /// </summary>
    Task<(int articleId, string message, bool vectorSuccess)> ConvertToKbAsync(Guid ticketId, string userId, string tenantId, bool triggerVectorIndex = true);
}
