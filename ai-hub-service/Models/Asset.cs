using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace ai_hub_service.Models;

/// <summary>
/// 附件表实体（kb_asset）
/// </summary>
[Table("kb_asset")]
public class Asset
{
    /// <summary>
    /// 主键ID
    /// </summary>
    [Key]
    [Column("id")]
    public int Id { get; set; }

    /// <summary>
    /// 租户ID
    /// </summary>
    [MaxLength(50)]
    [Column("tenant_id")]
    public string? TenantId { get; set; }

    /// <summary>
    /// 关联的知识条目ID
    /// </summary>
    [Required]
    [Column("article_id")]
    public int ArticleId { get; set; }

    /// <summary>
    /// 资产类型：image/video/pdf/other
    /// </summary>
    [Required]
    [MaxLength(50)]
    [Column("asset_type")]
    public string AssetType { get; set; } = string.Empty;

    /// <summary>
    /// 文件名
    /// </summary>
    [Required]
    [MaxLength(500)]
    [Column("file_name")]
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// URL（OSS/本地路径）
    /// </summary>
    [Required]
    [MaxLength(1000)]
    [Column("url")]
    public string Url { get; set; } = string.Empty;

    /// <summary>
    /// 文件大小（字节）
    /// </summary>
    [Column("size")]
    public long Size { get; set; }

    /// <summary>
    /// 视频时长（秒，可选）
    /// </summary>
    [Column("duration")]
    public int? Duration { get; set; }

    /// <summary>
    /// 创建时间
    /// </summary>
    [Required]
    [Column("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.Now;

    /// <summary>
    /// 删除时间（软删除标记，NULL表示未删除）
    /// </summary>
    [Column("deleted_at")]
    public DateTime? DeletedAt { get; set; }

    // 导航属性
    /// <summary>
    /// 关联的知识条目
    /// </summary>
    public virtual KnowledgeArticle Article { get; set; } = null!;
}
