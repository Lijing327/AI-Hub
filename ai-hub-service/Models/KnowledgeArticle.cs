using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace ai_hub_service.Models;

/// <summary>
/// 知识主表实体（kb_article）
/// </summary>
[Table("kb_article")]
public class KnowledgeArticle
{
    /// <summary>
    /// 主键ID
    /// </summary>
    [Key]
    [Column("id")]
    public int Id { get; set; }

    /// <summary>
    /// 来源类型（如：ticket, manual）
    /// 需执行迁移 010_AddSourceFieldsToKbArticle.sql 后，数据库才有此列；未迁移前用 NotMapped 避免查询报错
    /// </summary>
    [MaxLength(50)]
    [Column("source_type")]
    [NotMapped]
    public string? SourceType { get; set; }

    /// <summary>
    /// 来源ID（对应 source_type 的ID）
    /// 需执行迁移 010_AddSourceFieldsToKbArticle.sql 后，数据库才有此列；未迁移前用 NotMapped 避免查询报错
    /// </summary>
    [MaxLength(50)]
    [Column("source_id")]
    [NotMapped]
    public string? SourceId { get; set; }

    /// <summary>
    /// 租户ID
    /// </summary>
    [MaxLength(50)]
    [Column("tenant_id")]
    public string? TenantId { get; set; }

    /// <summary>
    /// 知识标题
    /// </summary>
    [Required]
    [MaxLength(500)]
    [Column("title")]
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// 用户问题/现象描述：尽量贴近用户口语
    /// </summary>
    [Column("question_text")]
    public string? QuestionText { get; set; }

    /// <summary>
    /// 原因分析：可写"可能原因1/2/3"
    /// </summary>
    [Column("cause_text")]
    public string? CauseText { get; set; }

    /// <summary>
    /// 解决步骤：结构化分步更好
    /// </summary>
    [Column("solution_text")]
    public string? SolutionText { get; set; }

    /// <summary>
    /// 适用范围：机型/版本/模块/场景（JSON格式）
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
    /// 版本号（整数）
    /// </summary>
    [Column("version")]
    public int Version { get; set; } = 1;

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

    /// <summary>
    /// 删除时间（软删除标记，NULL表示未删除）
    /// </summary>
    [Column("deleted_at")]
    public DateTime? DeletedAt { get; set; }

    // 导航属性
    /// <summary>
    /// 附件列表
    /// </summary>
    public virtual ICollection<Asset> Assets { get; set; } = new List<Asset>();

    /// <summary>
    /// 知识块列表
    /// </summary>
    public virtual ICollection<KnowledgeChunk> Chunks { get; set; } = new List<KnowledgeChunk>();
}
