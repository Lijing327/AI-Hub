using ai_hub_service.DTOs;

namespace ai_hub_service.Services;

/// <summary>
/// 知识条目服务接口
/// </summary>
public interface IKnowledgeItemService
{
    Task<KnowledgeItemDto?> GetByIdAsync(int id);
    Task<PagedResultDto<KnowledgeItemDto>> SearchAsync(SearchKnowledgeItemDto searchDto);
    Task<KnowledgeItemDto> CreateAsync(CreateKnowledgeItemDto createDto);
    Task<KnowledgeItemDto?> UpdateAsync(int id, UpdateKnowledgeItemDto updateDto);
    Task<bool> DeleteAsync(int id);
    Task<bool> PublishAsync(int id);
}
