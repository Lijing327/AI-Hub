using ai_hub_service.DTOs;

namespace ai_hub_service.Services;

/// <summary>
/// 附件服务接口（kb_asset）
/// </summary>
public interface IAssetService
{
    Task<AssetDto> UploadAsync(int articleId, IFormFile file);
    Task<bool> DeleteAsync(int assetId); // 软删除
    Task<bool> RestoreAsync(int assetId); // 恢复已删除的记录
    Task<List<AssetDto>> GetByArticleIdAsync(int articleId);
}
