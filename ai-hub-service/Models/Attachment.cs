using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace ai_hub_service.Models;

/// <summary>
/// 附件实体
/// </summary>
[Table("kb_attachment")]
public class Attachment
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
    /// 文件名
    /// </summary>
    [Required]
    [MaxLength(500)]
    [Column("file_name")]
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// 文件存储路径
    /// </summary>
    [Required]
    [MaxLength(1000)]
    [Column("file_path")]
    public string FilePath { get; set; } = string.Empty;

    /// <summary>
    /// 文件访问URL
    /// </summary>
    [Required]
    [MaxLength(1000)]
    [Column("file_url")]
    public string FileUrl { get; set; } = string.Empty;

    /// <summary>
    /// 文件类型（image/video/pdf等）
    /// </summary>
    [Required]
    [MaxLength(50)]
    [Column("file_type")]
    public string FileType { get; set; } = string.Empty;

    /// <summary>
    /// 文件大小（字节）
    /// </summary>
    [Column("file_size")]
    public long FileSize { get; set; }

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
