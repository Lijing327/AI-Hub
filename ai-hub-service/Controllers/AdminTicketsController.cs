using Microsoft.AspNetCore.Mvc;
using AiHub.DTOs;
using AiHub.Models;
using AiHub.Services;
using ai_hub_service.Controllers;
using ai_hub_service.DTOs;

namespace AiHub.Controllers;

/// <summary>
/// 工单管理控制器（公司内部均可访问，暂不校验登录）
/// </summary>
[ApiController]
[Route("api/admin/tickets")]
public class AdminTicketsController : BaseController
{
    private readonly ITicketService _ticketService;
    private readonly ILogger<AdminTicketsController> _logger;

    public AdminTicketsController(ITicketService ticketService, ILogger<AdminTicketsController> logger)
    {
        _ticketService = ticketService;
        _logger = logger;
    }

    /// <summary>
    /// 获取所有工单列表
    /// GET: /api/admin/tickets?pageIndex=1&pageSize=20&status=pending
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<PagedResultDto<TicketListDto>>> List([FromQuery] TicketQueryRequest query)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation("查看工单列表 - UserId: {UserId}, Page: {Page}", userId, query.PageIndex);

            var result = await _ticketService.ListAsync(query, userId, tenantId, isStaff: true);

            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "获取工单列表失败");
            return StatusCode(500, new { error = "获取工单列表失败", message = ex.Message });
        }
    }

    /// <summary>
    /// 获取工单详情（包含 AI 会话信息）
    /// GET: /api/admin/tickets/{id}
    /// </summary>
    [HttpGet("{id}")]
    public async Task<ActionResult<TicketDetailDto>> GetById(Guid id)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation("查看工单详情 - TicketId: {TicketId}, UserId: {UserId}", id, userId);

            // 默认包含 AI 会话信息
            var ticket = await _ticketService.GetByIdAsync(id, userId, tenantId, isStaff: true);

            if (ticket == null)
                return NotFound(new { error = "工单不存在" });

            return Ok(ticket);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "获取工单详情失败 - TicketId: {TicketId}", id);
            return StatusCode(500, new { error = "获取工单详情失败", message = ex.Message });
        }
    }

    /// <summary>
    /// 开始处理工单
    /// POST: /api/admin/tickets/{id}/start
    /// </summary>
    [HttpPost("{id}/start")]
    public async Task<ActionResult<TicketDetailDto>> Start(Guid id, [FromBody] StartTicketRequest? request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation("开始处理工单 - TicketId: {TicketId}, UserId: {UserId}", id, userId);

            var ticket = await _ticketService.StartAsync(id, request, userId, tenantId);

            if (ticket == null)
                return NotFound(new { error = "工单不存在" });

            return Ok(ticket);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning(ex, "开始处理失败 - TicketId: {TicketId}: {Message}", id, ex.Message);
            return BadRequest(new { error = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "开始处理时发生错误 - TicketId: {TicketId}", id);
            return StatusCode(500, new { error = "操作失败", message = ex.Message });
        }
    }

    /// <summary>
    /// 标记工单已解决
    /// POST: /api/admin/tickets/{id}/resolve
    /// </summary>
    [HttpPost("{id}/resolve")]
    public async Task<ActionResult<TicketDetailDto>> Resolve(Guid id, [FromBody] ResolveTicketRequest request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation("解决工单 - TicketId: {TicketId}, UserId: {UserId}", id, userId);

            // 验证 final_solution_summary 必填
            if (string.IsNullOrWhiteSpace(request.FinalSolutionSummary))
            {
                return BadRequest(new { error = "解决方案摘要不能为空" });
            }

            var ticket = await _ticketService.ResolveAsync(id, request, userId, tenantId);

            if (ticket == null)
                return NotFound(new { error = "工单不存在" });

            return Ok(ticket);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning(ex, "解决失败 - TicketId: {TicketId}: {Message}", id, ex.Message);
            return BadRequest(new { error = ex.Message });
        }
        catch (ArgumentException ex)
        {
            _logger.LogWarning(ex, "解决参数错误 - TicketId: {TicketId}: {Message}", id, ex.Message);
            return BadRequest(new { error = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "解决时发生错误 - TicketId: {TicketId}", id);
            return StatusCode(500, new { error = "操作失败", message = ex.Message });
        }
    }

    /// <summary>
    /// 关闭工单
    /// POST: /api/admin/tickets/{id}/close
    /// </summary>
    [HttpPost("{id}/close")]
    public async Task<ActionResult<TicketDetailDto>> Close(Guid id, [FromBody] CloseTicketRequest? request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation("关闭工单 - TicketId: {TicketId}, UserId: {UserId}", id, userId);

            var ticket = await _ticketService.CloseAsync(id, request, userId, tenantId);

            if (ticket == null)
                return NotFound(new { error = "工单不存在" });

            return Ok(ticket);
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning(ex, "关闭失败 - TicketId: {TicketId}: {Message}", id, ex.Message);
            return BadRequest(new { error = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "关闭时发生错误 - TicketId: {TicketId}", id);
            return StatusCode(500, new { error = "操作失败", message = ex.Message });
        }
    }

    /// <summary>
    /// 添加工单日志/备注
    /// POST: /api/admin/tickets/{id}/logs
    /// </summary>
    [HttpPost("{id}/logs")]
    public async Task<ActionResult<TicketLogDto>> AddLog(Guid id, [FromBody] CreateTicketLogRequest request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation("添加工单日志 - TicketId: {TicketId}, UserId: {UserId}", id, userId);

            var log = await _ticketService.AddLogAsync(id, request, userId, tenantId);

            return Ok(log);
        }
        catch (KeyNotFoundException ex)
        {
            _logger.LogWarning(ex, "添加日志失败 - TicketId: {TicketId}: {Message}", id, ex.Message);
            return NotFound(new { error = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "添加日志时发生错误 - TicketId: {TicketId}", id);
            return StatusCode(500, new { error = "操作失败", message = ex.Message });
        }
    }

    /// <summary>
    /// 将工单转换为知识库文章
    /// POST: /api/admin/tickets/{id}/convert-to-kb
    /// </summary>
    [HttpPost("{id}/convert-to-kb")]
    public async Task<ActionResult> ConvertToKb(Guid id, [FromBody] ConvertToKbRequest? request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();
            var triggerVectorIndex = request?.TriggerVectorIndex ?? true;

            _logger.LogInformation("转知识库 - TicketId: {TicketId}, UserId: {UserId}, TriggerVector: {Trigger}",
                id, userId, triggerVectorIndex);

            var result = await _ticketService.ConvertToKbAsync(
                id, userId, tenantId, triggerVectorIndex);

            return Ok(new
            {
                message = result.message,
                articleId = result.articleId,
                vectorSuccess = result.vectorSuccess,
                vectorMessage = result.vectorSuccess ? "向量入库成功" : "向量入库失败，请查看工单日志"
            });
        }
        catch (KeyNotFoundException ex)
        {
            _logger.LogWarning(ex, "转知识库失败 - TicketId: {TicketId}: {Message}", id, ex.Message);
            return NotFound(new { error = ex.Message });
        }
        catch (InvalidOperationException ex)
        {
            _logger.LogWarning(ex, "转知识库失败 - TicketId: {TicketId}: {Message}", id, ex.Message);
            return BadRequest(new { error = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "转知识库时发生错误 - TicketId: {TicketId}", id);
            return StatusCode(500, new { error = "操作失败", message = ex.Message });
        }
    }
}
