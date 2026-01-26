namespace ai_hub_service.DTOs;

/// <summary>
/// 批量创建知识条目请求 DTO（内部 API）
/// </summary>
public class BatchCreateArticlesRequestDto
{
    public List<CreateKnowledgeArticleDto> Articles { get; set; } = new();
}

/// <summary>
/// 批量创建知识条目响应 DTO
/// </summary>
public class BatchCreateArticlesResponseDto
{
    public int SuccessCount { get; set; }
    public int FailureCount { get; set; }
    public List<BatchCreateResultItemDto> Results { get; set; } = new();
}

/// <summary>
/// 批量创建结果项
/// </summary>
public class BatchCreateResultItemDto
{
    public int Index { get; set; }
    public bool Success { get; set; }
    public int? ArticleId { get; set; }
    public string? Error { get; set; }
}

/// <summary>
/// 批量发布请求 DTO
/// </summary>
public class BatchPublishArticlesRequestDto
{
    public List<int> ArticleIds { get; set; } = new();
}

/// <summary>
/// 批量发布响应 DTO
/// </summary>
public class BatchPublishArticlesResponseDto
{
    public int SuccessCount { get; set; }
    public int FailureCount { get; set; }
    public List<BatchPublishResultItemDto> Results { get; set; } = new();
}

/// <summary>
/// 批量发布结果项
/// </summary>
public class BatchPublishResultItemDto
{
    public int ArticleId { get; set; }
    public bool Success { get; set; }
    public string? Error { get; set; }
}

/// <summary>
/// 批量创建附件请求 DTO（内部 API）
/// </summary>
public class BatchCreateAssetsRequestDto
{
    public List<CreateAssetDto> Assets { get; set; } = new();
}

/// <summary>
/// 创建附件 DTO（内部 API）
/// </summary>
public class CreateAssetDto
{
    public int ArticleId { get; set; }
    public string AssetType { get; set; } = string.Empty; // image/video/pdf/other
    public string FileName { get; set; } = string.Empty;
    public string Url { get; set; } = string.Empty; // 文件访问 URL
    public long Size { get; set; }
    public int? Duration { get; set; } // 视频时长（秒，可选）
}

/// <summary>
/// 批量创建附件响应 DTO
/// </summary>
public class BatchCreateAssetsResponseDto
{
    public int SuccessCount { get; set; }
    public int FailureCount { get; set; }
    public List<BatchCreateAssetResultItemDto> Results { get; set; } = new();
}

/// <summary>
/// 批量创建附件结果项
/// </summary>
public class BatchCreateAssetResultItemDto
{
    public int Index { get; set; }
    public bool Success { get; set; }
    public int? AssetId { get; set; }
    public string? Error { get; set; }
}
