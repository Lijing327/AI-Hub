namespace ai_hub_service.DTOs;

/// <summary>
/// 附件DTO
/// </summary>
public class AttachmentDto
{
    public int Id { get; set; }
    public int KnowledgeItemId { get; set; }
    public string FileName { get; set; } = string.Empty;
    public string FileUrl { get; set; } = string.Empty;
    public string FileType { get; set; } = string.Empty;
    public long FileSize { get; set; }
    public DateTime CreatedAt { get; set; }
}
