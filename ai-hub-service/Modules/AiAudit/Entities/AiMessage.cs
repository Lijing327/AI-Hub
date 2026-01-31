namespace ai_hub_service.Modules.AiAudit.Entities;

/// <summary>
/// AI 消息表
/// </summary>
public class AiMessage
{
    /// <summary>消息 ID（UUID）</summary>
    public Guid MessageId { get; set; }

    /// <summary>会话 ID</summary>
    public Guid ConversationId { get; set; }

    /// <summary>角色：user/assistant/system</summary>
    public string Role { get; set; } = "user";

    /// <summary>消息内容</summary>
    public string Content { get; set; } = "";

    /// <summary>内容长度</summary>
    public int ContentLen { get; set; }

    /// <summary>是否已脱敏</summary>
    public bool IsMasked { get; set; }

    /// <summary>脱敏后内容（可选）</summary>
    public string? MaskedContent { get; set; }

    /// <summary>创建时间（UTC）</summary>
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // 导航属性
    public AiConversation? Conversation { get; set; }
    public AiDecisionLog? DecisionLog { get; set; }
    public AiResponse? Response { get; set; }
    public ICollection<AiRetrievalLog> RetrievalLogs { get; set; } = new List<AiRetrievalLog>();
}
