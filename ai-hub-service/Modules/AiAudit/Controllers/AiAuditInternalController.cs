using ai_hub_service.Modules.AiAudit.Dtos;
using ai_hub_service.Modules.AiAudit.Services;
using Microsoft.AspNetCore.Mvc;

namespace ai_hub_service.Modules.AiAudit.Controllers;

/// <summary>
/// AI 审计内部 API（供 Python 调用，走 X-Internal-Token 鉴权）
/// </summary>
[ApiController]
[Route("internal/ai-audit")]
[Tags("AI 审计（内部）")]
public class AiAuditInternalController : ControllerBase
{
    private readonly IAiAuditService _auditService;

    public AiAuditInternalController(IAiAuditService auditService)
    {
        _auditService = auditService;
    }

    /// <summary>创建会话</summary>
    [HttpPost("conversation/start")]
    public async Task<ActionResult<StartConversationResponse>> StartConversation([FromBody] StartConversationRequest request)
    {
        var result = await _auditService.StartConversationAsync(request);
        return Ok(result);
    }

    /// <summary>追加消息</summary>
    [HttpPost("message")]
    public async Task<ActionResult<AppendMessageResponse>> AppendMessage([FromBody] AppendMessageRequest request)
    {
        var result = await _auditService.AppendMessageAsync(request);
        return Ok(result);
    }

    /// <summary>记录决策</summary>
    [HttpPost("decision")]
    public async Task<ActionResult<AuditOperationResponse>> LogDecision([FromBody] LogDecisionRequest request)
    {
        var result = await _auditService.LogDecisionAsync(request);
        return Ok(result);
    }

    /// <summary>记录 RAG 检索</summary>
    [HttpPost("retrieval")]
    public async Task<ActionResult<AuditOperationResponse>> LogRetrieval([FromBody] LogRetrievalRequest request)
    {
        var result = await _auditService.LogRetrievalAsync(request);
        return Ok(result);
    }

    /// <summary>记录响应</summary>
    [HttpPost("response")]
    public async Task<ActionResult<AuditOperationResponse>> LogResponse([FromBody] LogResponseRequest request)
    {
        var result = await _auditService.LogResponseAsync(request);
        return Ok(result);
    }

    /// <summary>结束会话</summary>
    [HttpPost("conversation/end")]
    public async Task<ActionResult<AuditOperationResponse>> EndConversation([FromBody] EndConversationRequest request)
    {
        var result = await _auditService.EndConversationAsync(request);
        return Ok(result);
    }
}
