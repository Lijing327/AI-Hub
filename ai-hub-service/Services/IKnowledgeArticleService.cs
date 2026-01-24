using ai_hub_service.DTOs;

namespace ai_hub_service.Services;

/// <summary>
/// 知识主表服务接口
/// </summary>
public interface IKnowledgeArticleService
{
    Task<KnowledgeArticleDto?> GetByIdAsync(int id);
    Task<PagedResultDto<KnowledgeArticleDto>> SearchAsync(SearchKnowledgeArticleDto searchDto);
    Task<KnowledgeArticleDto> CreateAsync(CreateKnowledgeArticleDto createDto);
    Task<KnowledgeArticleDto?> UpdateAsync(int id, UpdateKnowledgeArticleDto updateDto);
    Task<bool> DeleteAsync(int id); // 软删除
    Task<bool> RestoreAsync(int id); // 恢复已删除的记录
    Task<bool> PublishAsync(int id);
}
