using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace ai_hub_service.Models;

/// <summary>
/// 知识块实体（用于向量化）
/// </summary>
[Table("kb_chunk")]
public class KnowledgeChunk
{
    /// <summary>
    /// 主键ID
    /// </summary>
    [Key]
    [Column("id")]
    public int Id { get; set; }

    /// <summary>
    /// 关联的知识条目ID
    /// </summary>
    [Required]
    [Column("knowledge_item_id")]
    public int KnowledgeItemId { get; set; }

    /// <summary>
    /// 块文本内容
    /// </summary>
    [Required]
    [Column("chunk_text")]
    public string ChunkText { get; set; } = string.Empty;

    /// <summary>
    /// 块索引（同一知识条目中的顺序）
    /// </summary>
    [Required]
    [Column("chunk_index")]
    public int ChunkIndex { get; set; }

    /// <summary>
    /// 创建时间
    /// </summary>
    [Required]
    [Column("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.Now;

    // 导航属性
    /// <summary>
    /// 关联的知识条目
    /// </summary>
    public virtual KnowledgeItem KnowledgeItem { get; set; } = null!;
}
