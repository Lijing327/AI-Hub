using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace ai_hub_service.Models;

/// <summary>
/// 知识条目实体
/// </summary>
[Table("kb_item")]
public class KnowledgeItem
{
    /// <summary>
    /// 主键ID
    /// </summary>
    [Key]
    [Column("id")]
    public int Id { get; set; }

    /// <summary>
    /// 标题
    /// </summary>
    [Required]
    [MaxLength(500)]
    [Column("title")]
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// 问题描述
    /// </summary>
    [Column("question_text")]
    public string? QuestionText { get; set; }

    /// <summary>
    /// 原因分析
    /// </summary>
    [Column("cause_text")]
    public string? CauseText { get; set; }

    /// <summary>
    /// 解决方案
    /// </summary>
    [Column("solution_text")]
    public string? SolutionText { get; set; }

    /// <summary>
    /// 适用范围（JSON格式）
    /// </summary>
    [Column("scope_json")]
    public string? ScopeJson { get; set; }

    /// <summary>
    /// 标签（逗号分隔）
    /// </summary>
    [MaxLength(1000)]
    [Column("tags")]
    public string? Tags { get; set; }

    /// <summary>
    /// 状态：draft/published/archived
    /// </summary>
    [Required]
    [MaxLength(20)]
    [Column("status")]
    public string Status { get; set; } = "draft";

    /// <summary>
    /// 版本号
    /// </summary>
    [Column("version")]
    public int Version { get; set; } = 1;

    /// <summary>
    /// 租户ID
    /// </summary>
    [MaxLength(50)]
    [Column("tenant_id")]
    public string? TenantId { get; set; }

    /// <summary>
    /// 创建人
    /// </summary>
    [MaxLength(100)]
    [Column("created_by")]
    public string? CreatedBy { get; set; }

    /// <summary>
    /// 创建时间
    /// </summary>
    [Required]
    [Column("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.Now;

    /// <summary>
    /// 更新时间
    /// </summary>
    [Column("updated_at")]
    public DateTime? UpdatedAt { get; set; }

    /// <summary>
    /// 发布时间
    /// </summary>
    [Column("published_at")]
    public DateTime? PublishedAt { get; set; }

    // 导航属性
    /// <summary>
    /// 附件列表
    /// </summary>
    public virtual ICollection<Attachment> Attachments { get; set; } = new List<Attachment>();

    /// <summary>
    /// 知识块列表
    /// </summary>
    public virtual ICollection<KnowledgeChunk> Chunks { get; set; } = new List<KnowledgeChunk>();
}
