namespace ai_hub_service.Modules.AiAudit.Entities;

/// <summary>
/// RAG 命中文档日志
/// </summary>
public class AiRetrievalLog
{
    /// <summary>自增主键</summary>
    public long Id { get; set; }

    /// <summary>消息 ID</summary>
    public Guid MessageId { get; set; }

    /// <summary>文档 ID</summary>
    public string DocId { get; set; } = "";

    /// <summary>文档标题</summary>
    public string? DocTitle { get; set; }

    /// <summary>相似度分数</summary>
    public decimal Score { get; set; }

    /// <summary>排名（1 表示最相关）</summary>
    public int Rank { get; set; }

    /// <summary>Chunk ID（可选）</summary>
    public string? ChunkId { get; set; }

    /// <summary>创建时间（UTC）</summary>
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // 导航属性
    public AiMessage? Message { get; set; }
}
