namespace ai_hub_service.Modules.AiAudit.Entities;

/// <summary>
/// AI 会话主表
/// </summary>
public class AiConversation
{
    /// <summary>会话 ID（UUID）</summary>
    public Guid ConversationId { get; set; }

    /// <summary>租户 ID</summary>
    public string TenantId { get; set; } = "default";

    /// <summary>用户 ID（可选）</summary>
    public string? UserId { get; set; }

    /// <summary>渠道：web/app/wechat/api</summary>
    public string Channel { get; set; } = "web";

    /// <summary>会话开始时间（UTC）</summary>
    public DateTime StartedAt { get; set; } = DateTime.UtcNow;

    /// <summary>会话结束时间（UTC）</summary>
    public DateTime? EndedAt { get; set; }

    /// <summary>扩展元数据（JSON：设备/版本/IP等）</summary>
    public string? MetaJson { get; set; }

    /// <summary>创建时间（UTC）</summary>
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // 导航属性
    public ICollection<AiMessage> Messages { get; set; } = new List<AiMessage>();
}
