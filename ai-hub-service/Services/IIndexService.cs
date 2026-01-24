namespace ai_hub_service.Services;

/// <summary>
/// 向量化索引服务接口
/// </summary>
public interface IIndexService
{
    Task UpsertEmbeddingsAsync(List<string> chunks);
}
