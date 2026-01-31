namespace ai_hub_service.Modules.AiAudit.Entities;

/// <summary>
/// AI 最终响应日志
/// </summary>
public class AiResponse
{
    /// <summary>消息 ID（主键，与 AiMessage 1:1）</summary>
    public Guid MessageId { get; set; }

    /// <summary>最终回答内容</summary>
    public string? FinalAnswer { get; set; }

    /// <summary>响应耗时（毫秒）</summary>
    public int ResponseTimeMs { get; set; }

    /// <summary>是否成功</summary>
    public bool IsSuccess { get; set; } = true;

    /// <summary>错误类型：model_error/timeout/no_match...</summary>
    public string? ErrorType { get; set; }

    /// <summary>错误详情</summary>
    public string? ErrorDetail { get; set; }

    /// <summary>创建时间（UTC）</summary>
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // 导航属性
    public AiMessage? Message { get; set; }
}
