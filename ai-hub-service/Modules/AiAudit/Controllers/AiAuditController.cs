using ai_hub_service.Modules.AiAudit.Dtos;
using ai_hub_service.Modules.AiAudit.Services;
using Microsoft.AspNetCore.Mvc;

namespace ai_hub_service.Modules.AiAudit.Controllers;

/// <summary>
/// AI 审计管理 API（供管理后台查询）
/// </summary>
[ApiController]
[Route("api/ai-audit")]
[Tags("AI 审计（管理）")]
public class AiAuditController : ControllerBase
{
    private readonly IAiAuditService _auditService;

    public AiAuditController(IAiAuditService auditService)
    {
        _auditService = auditService;
    }

    /// <summary>查询会话列表</summary>
    [HttpGet("conversations")]
    public async Task<ActionResult<object>> GetConversationList([FromQuery] ConversationListQuery query)
    {
        var (items, totalCount) = await _auditService.GetConversationListAsync(query);
        return Ok(new
        {
            items,
            totalCount,
            page = query.Page,
            pageSize = query.PageSize,
            totalPages = (int)Math.Ceiling(totalCount / (double)query.PageSize)
        });
    }

    /// <summary>获取会话详情（含所有消息和日志）</summary>
    [HttpGet("conversations/{conversationId}")]
    public async Task<ActionResult<ConversationDetail>> GetConversationDetail(Guid conversationId)
    {
        var detail = await _auditService.GetConversationDetailAsync(conversationId);
        if (detail == null)
            return NotFound(new { message = "会话不存在" });
        return Ok(detail);
    }

    // ========== 统计 API ==========

    /// <summary>获取统计概览</summary>
    [HttpGet("stats/overview")]
    public async Task<ActionResult<StatsOverview>> GetStatsOverview([FromQuery] StatsQuery query)
    {
        var overview = await _auditService.GetStatsOverviewAsync(query);
        return Ok(overview);
    }

    /// <summary>获取 Top 意图统计</summary>
    [HttpGet("stats/top-intents")]
    public async Task<ActionResult<List<IntentStat>>> GetTopIntents([FromQuery] StatsQuery query, [FromQuery] int top = 10)
    {
        var intents = await _auditService.GetTopIntentsAsync(query, top);
        return Ok(intents);
    }

    /// <summary>获取 Top 命中文档统计</summary>
    [HttpGet("stats/top-docs")]
    public async Task<ActionResult<List<DocHitStat>>> GetTopDocs([FromQuery] StatsQuery query, [FromQuery] int top = 10)
    {
        var docs = await _auditService.GetTopDocsAsync(query, top);
        return Ok(docs);
    }

    /// <summary>获取无命中问题列表</summary>
    [HttpGet("stats/no-match")]
    public async Task<ActionResult<List<NoMatchQuestion>>> GetNoMatchQuestions([FromQuery] StatsQuery query, [FromQuery] int top = 50)
    {
        var questions = await _auditService.GetNoMatchQuestionsAsync(query, top);
        return Ok(questions);
    }
}
