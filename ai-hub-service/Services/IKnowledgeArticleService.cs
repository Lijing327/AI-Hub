using ai_hub_service.DTOs;

namespace ai_hub_service.Services;

/// <summary>
/// 知识主表服务接口
/// </summary>
public interface IKnowledgeArticleService
{
    Task<KnowledgeArticleDto?> GetByIdAsync(int id, string tenantId);
    Task<PagedResultDto<KnowledgeArticleDto>> SearchAsync(SearchKnowledgeArticleDto searchDto, string tenantId);
    Task<KnowledgeArticleDto> CreateAsync(CreateKnowledgeArticleDto createDto, string tenantId);
    Task<KnowledgeArticleDto?> UpdateAsync(int id, UpdateKnowledgeArticleDto updateDto, string tenantId);
    Task<bool> DeleteAsync(int id, string tenantId); // 软删除
    Task<bool> RestoreAsync(int id, string tenantId); // 恢复已删除的记录
    Task<bool> PublishAsync(int id, string tenantId);
}
