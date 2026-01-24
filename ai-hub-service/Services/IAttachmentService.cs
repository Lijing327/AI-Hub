using ai_hub_service.DTOs;

namespace ai_hub_service.Services;

/// <summary>
/// 附件服务接口
/// </summary>
public interface IAttachmentService
{
    Task<AttachmentDto> UploadAsync(int knowledgeItemId, IFormFile file);
    Task<bool> DeleteAsync(int attachmentId);
    Task<List<AttachmentDto>> GetByKnowledgeItemIdAsync(int knowledgeItemId);
}
