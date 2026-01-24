namespace ai_hub_service.DTOs;

/// <summary>
/// 附件DTO（kb_asset）
/// </summary>
public class AssetDto
{
    public int Id { get; set; }
    public string? TenantId { get; set; }
    public int ArticleId { get; set; }
    public string AssetType { get; set; } = string.Empty; // image/video/pdf/other
    public string FileName { get; set; } = string.Empty;
    public string Url { get; set; } = string.Empty; // OSS/本地路径
    public long Size { get; set; }
    public int? Duration { get; set; } // 视频时长（秒，可选）
    public DateTime CreatedAt { get; set; }
    public DateTime? DeletedAt { get; set; } // 删除时间（软删除标记）
}
