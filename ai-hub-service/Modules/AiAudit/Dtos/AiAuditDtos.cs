namespace ai_hub_service.Modules.AiAudit.Dtos;

// ========== 请求 DTO ==========

/// <summary>创建会话请求</summary>
public class StartConversationRequest
{
    public string TenantId { get; set; } = "default";
    public string? UserId { get; set; }
    public string Channel { get; set; } = "web";
    public string? MetaJson { get; set; }
}

/// <summary>追加消息请求</summary>
public class AppendMessageRequest
{
    public Guid ConversationId { get; set; }
    public string Role { get; set; } = "user";
    public string Content { get; set; } = "";
    public bool IsMasked { get; set; }
    public string? MaskedContent { get; set; }
}

/// <summary>记录决策请求</summary>
public class LogDecisionRequest
{
    public Guid MessageId { get; set; }
    public string IntentType { get; set; } = "chat";
    public decimal Confidence { get; set; }
    public string? ModelName { get; set; }
    public string? PromptVersion { get; set; }
    public bool UseKnowledge { get; set; }
    public string? FallbackReason { get; set; }
    public int? TokensIn { get; set; }
    public int? TokensOut { get; set; }
}

/// <summary>RAG 命中文档项</summary>
public class RetrievalDocItem
{
    public string DocId { get; set; } = "";
    public string? DocTitle { get; set; }
    public decimal Score { get; set; }
    public int Rank { get; set; }
    public string? ChunkId { get; set; }
}

/// <summary>记录 RAG 检索请求</summary>
public class LogRetrievalRequest
{
    public Guid MessageId { get; set; }
    public List<RetrievalDocItem> Docs { get; set; } = new();
}

/// <summary>记录响应请求</summary>
public class LogResponseRequest
{
    public Guid MessageId { get; set; }
    public string? FinalAnswer { get; set; }
    public int ResponseTimeMs { get; set; }
    public bool IsSuccess { get; set; } = true;
    public string? ErrorType { get; set; }
    public string? ErrorDetail { get; set; }
}

/// <summary>结束会话请求</summary>
public class EndConversationRequest
{
    public Guid ConversationId { get; set; }
}

// ========== 响应 DTO ==========

/// <summary>创建会话响应</summary>
public class StartConversationResponse
{
    public Guid ConversationId { get; set; }
    public DateTime StartedAt { get; set; }
}

/// <summary>追加消息响应</summary>
public class AppendMessageResponse
{
    public Guid MessageId { get; set; }
    public DateTime CreatedAt { get; set; }
}

/// <summary>通用操作响应</summary>
public class AuditOperationResponse
{
    public bool Success { get; set; } = true;
    public string? Message { get; set; }
}

// ========== 查询 DTO ==========

/// <summary>会话列表查询</summary>
public class ConversationListQuery
{
    public string? TenantId { get; set; }
    public string? UserId { get; set; }
    public string? Channel { get; set; }
    public string? IntentType { get; set; }
    public bool? HasFallback { get; set; }
    public DateTime? StartFrom { get; set; }
    public DateTime? StartTo { get; set; }
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
}

/// <summary>会话列表项</summary>
public class ConversationListItem
{
    public Guid ConversationId { get; set; }
    public string TenantId { get; set; } = "";
    public string? UserId { get; set; }
    public string Channel { get; set; } = "";
    public DateTime StartedAt { get; set; }
    public DateTime? EndedAt { get; set; }
    public int MessageCount { get; set; }
    public string? MainIntent { get; set; }
    public bool HasFallback { get; set; }
    public int? AvgResponseTimeMs { get; set; }
}

/// <summary>会话详情</summary>
public class ConversationDetail
{
    public Guid ConversationId { get; set; }
    public string TenantId { get; set; } = "";
    public string? UserId { get; set; }
    public string Channel { get; set; } = "";
    public DateTime StartedAt { get; set; }
    public DateTime? EndedAt { get; set; }
    public string? MetaJson { get; set; }
    public List<MessageDetail> Messages { get; set; } = new();
}

/// <summary>消息详情（含决策/检索/响应）</summary>
public class MessageDetail
{
    public Guid MessageId { get; set; }
    public string Role { get; set; } = "";
    public string Content { get; set; } = "";
    public DateTime CreatedAt { get; set; }
    public DecisionDetail? Decision { get; set; }
    public List<RetrievalDetail>? Retrievals { get; set; }
    public ResponseDetail? Response { get; set; }
}

/// <summary>决策详情</summary>
public class DecisionDetail
{
    public string IntentType { get; set; } = "";
    public decimal Confidence { get; set; }
    public string? ModelName { get; set; }
    public string? PromptVersion { get; set; }
    public bool UseKnowledge { get; set; }
    public string? FallbackReason { get; set; }
    public int? TokensIn { get; set; }
    public int? TokensOut { get; set; }
}

/// <summary>检索详情</summary>
public class RetrievalDetail
{
    public string DocId { get; set; } = "";
    public string? DocTitle { get; set; }
    public decimal Score { get; set; }
    public int Rank { get; set; }
}

/// <summary>响应详情</summary>
public class ResponseDetail
{
    public string? FinalAnswer { get; set; }
    public int ResponseTimeMs { get; set; }
    public bool IsSuccess { get; set; }
    public string? ErrorType { get; set; }
    public string? ErrorDetail { get; set; }
}

// ========== 统计 DTO ==========

/// <summary>统计查询参数</summary>
public class StatsQuery
{
    public string? TenantId { get; set; }
    public DateTime? StartFrom { get; set; }
    public DateTime? StartTo { get; set; }
}

/// <summary>统计概览</summary>
public class StatsOverview
{
    /// <summary>总会话数</summary>
    public int TotalConversations { get; set; }
    /// <summary>总消息数</summary>
    public int TotalMessages { get; set; }
    /// <summary>兜底率（有 fallback_reason 的比例）</summary>
    public decimal FallbackRate { get; set; }
    /// <summary>低置信度率（confidence < 0.5）</summary>
    public decimal LowConfidenceRate { get; set; }
    /// <summary>平均响应时间（毫秒）</summary>
    public int AvgResponseTimeMs { get; set; }
    /// <summary>成功率</summary>
    public decimal SuccessRate { get; set; }
    /// <summary>知识库使用率</summary>
    public decimal KnowledgeUsageRate { get; set; }
}

/// <summary>意图统计项</summary>
public class IntentStat
{
    public string IntentType { get; set; } = "";
    public int Count { get; set; }
    public decimal Percentage { get; set; }
}

/// <summary>文档命中统计项</summary>
public class DocHitStat
{
    public string DocId { get; set; } = "";
    public string? DocTitle { get; set; }
    public int HitCount { get; set; }
    public decimal AvgScore { get; set; }
}

/// <summary>无命中问题</summary>
public class NoMatchQuestion
{
    public Guid MessageId { get; set; }
    public string Question { get; set; } = "";
    public DateTime CreatedAt { get; set; }
    public string? FallbackReason { get; set; }
}
