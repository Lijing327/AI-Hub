namespace ai_hub_service.Modules.AiAudit.Entities;

/// <summary>
/// AI 决策过程日志
/// </summary>
public class AiDecisionLog
{
    /// <summary>消息 ID（主键，与 AiMessage 1:1）</summary>
    public Guid MessageId { get; set; }

    /// <summary>意图类型：chat/solution/consult/install/maintain...</summary>
    public string IntentType { get; set; } = "chat";

    /// <summary>置信度 0~1</summary>
    public decimal Confidence { get; set; }

    /// <summary>模型名称</summary>
    public string? ModelName { get; set; }

    /// <summary>Prompt 版本</summary>
    public string? PromptVersion { get; set; }

    /// <summary>是否使用知识库</summary>
    public bool UseKnowledge { get; set; }

    /// <summary>兜底原因：no_match/low_confidence/model_error...</summary>
    public string? FallbackReason { get; set; }

    /// <summary>输入 Token 数</summary>
    public int? TokensIn { get; set; }

    /// <summary>输出 Token 数</summary>
    public int? TokensOut { get; set; }

    /// <summary>创建时间（UTC）</summary>
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // 导航属性
    public AiMessage? Message { get; set; }
}
