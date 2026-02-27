using Microsoft.AspNetCore.Mvc;
using AiHub.DTOs;
using AiHub.Models;
using AiHub.Services;
using ai_hub_service.Controllers;
using ai_hub_service.DTOs;

namespace AiHub.Controllers;

/// <summary>
/// 工单控制器
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class TicketsController : BaseController
{
    private readonly ITicketService _ticketService;
    private readonly ILogger<TicketsController> _logger;

    public TicketsController(ITicketService ticketService, ILogger<TicketsController> logger)
    {
        _ticketService = ticketService;
        _logger = logger;
    }

    /// <summary>
    /// 获取当前用户是否为工程师/管理员
    /// </summary>
    private bool IsStaffUser()
    {
        // TODO: 从 JWT claim 中读取角色，暂时用 header 判断
        var role = HttpContext.User.FindFirst("role")?.Value;
        return role == "engineer" || role == "admin";
    }

    /// <summary>
    /// 获取当前用户 ID（从 JWT 或请求头）
    /// </summary>
    private string GetUserId()
    {
        var userId = User.FindFirst("user_id")?.Value;
        if (!string.IsNullOrWhiteSpace(userId))
            return userId;

        //  fallback: 从请求头获取
        userId = HttpContext.Request.Headers["X-User-Id"].ToString();
        return userId ?? "anonymous";
    }

    /// <summary>
    /// 创建工单
    /// POST: /api/tickets
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<TicketDetailDto>> Create([FromBody] CreateTicketRequest request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation(
                "收到创建工单请求 - TenantId: {TenantId}, UserId: {UserId}, Title: {Title}",
                tenantId, userId, request.Title);

            var ticket = await _ticketService.CreateAsync(request, userId, tenantId);

            return CreatedAtAction(nameof(GetById), new { id = ticket.TicketId }, ticket);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "创建工单时发生错误");
            return StatusCode(500, new { error = "创建工单失败", message = ex.Message });
        }
    }

    /// <summary>
    /// 获取工单列表（支持分页和筛选）
    /// GET: /api/tickets?pageIndex=1&pageSize=20&status=pending
    /// </summary>
    [HttpGet]
    public async Task<ActionResult<PagedResultDto<TicketListDto>>> List([FromQuery] TicketQueryRequest query)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();
            var isStaff = IsStaffUser();

            _logger.LogInformation(
                "收到工单列表请求 - TenantId: {TenantId}, UserId: {UserId}, IsStaff: {IsStaff}, Page: {Page}",
                tenantId, userId, isStaff, query.PageIndex);

            var result = await _ticketService.ListAsync(query, userId, tenantId, isStaff);

            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "获取工单列表时发生错误");
            return StatusCode(500, new { error = "获取工单列表失败", message = ex.Message });
        }
    }

    /// <summary>
    /// 获取工单详情
    /// GET: /api/tickets/{id}
    /// </summary>
    [HttpGet("{id}")]
    public async Task<ActionResult<TicketDetailDto>> GetById(Guid id)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();
            var isStaff = IsStaffUser();

            _logger.LogInformation(
                "收到工单详情请求 - TicketId: {TicketId}, UserId: {UserId}",
                id, userId);

            var ticket = await _ticketService.GetByIdAsync(id, userId, tenantId, isStaff);

            if (ticket == null)
                return NotFound(new { error = "工单不存在或无权限查看" });

            return Ok(ticket);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "获取工单详情时发生错误 - TicketId: {TicketId}", id);
            return StatusCode(500, new { error = "获取工单详情失败", message = ex.Message });
        }
    }

    /// <summary>
    /// 更新工单
    /// PUT: /api/tickets/{id}
    /// </summary>
    [HttpPut("{id}")]
    public async Task<ActionResult<TicketDetailDto>> Update(Guid id, [FromBody] UpdateTicketRequest request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation(
                "收到更新工单请求 - TicketId: {TicketId}, UserId: {UserId}",
                id, userId);

            var ticket = await _ticketService.UpdateAsync(id, request, userId, tenantId);

            if (ticket == null)
                return NotFound(new { error = "工单不存在" });

            return Ok(ticket);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "更新工单时发生错误 - TicketId: {TicketId}", id);
            return StatusCode(500, new { error = "更新工单失败", message = ex.Message });
        }
    }

    /// <summary>
    /// 开始处理工单
    /// POST: /api/tickets/{id}/start
    /// </summary>
    [HttpPost("{id}/start")]
    public async Task<ActionResult<TicketDetailDto>> Start(Guid id, [FromBody] StartTicketRequest? request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation(
                "收到开始处理请求 - TicketId: {TicketId}, UserId: {UserId}",
                id, userId);

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
    /// POST: /api/tickets/{id}/resolve
    /// </summary>
    [HttpPost("{id}/resolve")]
    public async Task<ActionResult<TicketDetailDto>> Resolve(Guid id, [FromBody] ResolveTicketRequest request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation(
                "收到解决请求 - TicketId: {TicketId}, UserId: {UserId}",
                id, userId);

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
    /// POST: /api/tickets/{id}/close
    /// </summary>
    [HttpPost("{id}/close")]
    public async Task<ActionResult<TicketDetailDto>> Close(Guid id, [FromBody] CloseTicketRequest? request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation(
                "收到关闭请求 - TicketId: {TicketId}, UserId: {UserId}",
                id, userId);

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
    /// POST: /api/tickets/{id}/logs
    /// </summary>
    [HttpPost("{id}/logs")]
    public async Task<ActionResult<TicketLogDto>> AddLog(Guid id, [FromBody] CreateTicketLogRequest request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation(
                "收到添加日志请求 - TicketId: {TicketId}, UserId: {UserId}",
                id, userId);

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
    /// 获取工单日志列表
    /// GET: /api/tickets/{id}/logs
    /// </summary>
    [HttpGet("{id}/logs")]
    public async Task<ActionResult<List<TicketLogDto>>> GetLogs(Guid id)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();

            _logger.LogInformation(
                "收到获取日志请求 - TicketId: {TicketId}, UserId: {UserId}",
                id, userId);

            var logs = await _ticketService.GetLogsAsync(id, userId, tenantId);

            return Ok(logs);
        }
        catch (KeyNotFoundException ex)
        {
            _logger.LogWarning(ex, "获取日志失败 - TicketId: {TicketId}: {Message}", id, ex.Message);
            return NotFound(new { error = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "获取日志时发生错误 - TicketId: {TicketId}", id);
            return StatusCode(500, new { error = "获取失败", message = ex.Message });
        }
    }

    /// <summary>
    /// 将工单转换为知识库文章
    /// POST: /api/tickets/{id}/convert-to-kb
    /// </summary>
    [HttpPost("{id}/convert-to-kb")]
    public async Task<ActionResult> ConvertToKb(Guid id, [FromBody] ConvertToKbRequest? request)
    {
        try
        {
            var userId = GetUserId();
            var tenantId = GetTenantId();
            var triggerVectorIndex = request?.TriggerVectorIndex ?? true;

            _logger.LogInformation(
                "收到转知识库请求 - TicketId: {TicketId}, UserId: {UserId}, TriggerVector: {Trigger}",
                id, userId, triggerVectorIndex);

            var (articleId, message, vectorSuccess) = await _ticketService.ConvertToKbAsync(
                id, userId, tenantId, triggerVectorIndex);

            return Ok(new
            {
                message,
                articleId,
                vectorSuccess,
                vectorMessage = vectorSuccess ? "向量入库成功" : "向量入库失败，请查看工单日志"
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
