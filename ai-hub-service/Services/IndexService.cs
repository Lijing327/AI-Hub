namespace ai_hub_service.Services;

/// <summary>
/// 向量化索引服务实现（占位）
/// </summary>
public class IndexService : IIndexService
{
    private readonly ILogger<IndexService> _logger;

    public IndexService(ILogger<IndexService> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// 将知识块向量化并入库（占位方法，仅打日志）
    /// </summary>
    public async Task UpsertEmbeddingsAsync(List<string> chunks)
    {
        _logger.LogInformation($"准备向量化 {chunks.Count} 个知识块");
        
        foreach (var chunk in chunks)
        {
            _logger.LogInformation($"处理知识块: {chunk.Substring(0, Math.Min(50, chunk.Length))}...");
        }

        // TODO: 后续接入向量数据库（如Milvus、Pinecone等）
        await Task.CompletedTask;
    }
}
