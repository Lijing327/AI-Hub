namespace ai_hub_service.DTOs;

/// <summary>
/// 知识条目DTO（用于API传输）
/// </summary>
public class KnowledgeItemDto
{
    public int Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? QuestionText { get; set; }
    public string? CauseText { get; set; }
    public string? SolutionText { get; set; }
    public string? ScopeJson { get; set; }
    public string? Tags { get; set; }
    public string Status { get; set; } = "draft";
    public int Version { get; set; } = 1;
    public string? TenantId { get; set; }
    public string? CreatedBy { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
    public DateTime? PublishedAt { get; set; }
    public List<AttachmentDto>? Attachments { get; set; }
}

/// <summary>
/// 创建知识条目请求DTO
/// </summary>
public class CreateKnowledgeItemDto
{
    public string Title { get; set; } = string.Empty;
    public string? QuestionText { get; set; }
    public string? CauseText { get; set; }
    public string? SolutionText { get; set; }
    public string? ScopeJson { get; set; }
    public string? Tags { get; set; }
    public string? TenantId { get; set; }
    public string? CreatedBy { get; set; }
}

/// <summary>
/// 更新知识条目请求DTO
/// </summary>
public class UpdateKnowledgeItemDto
{
    public string Title { get; set; } = string.Empty;
    public string? QuestionText { get; set; }
    public string? CauseText { get; set; }
    public string? SolutionText { get; set; }
    public string? ScopeJson { get; set; }
    public string? Tags { get; set; }
}

/// <summary>
/// 搜索请求DTO
/// </summary>
public class SearchKnowledgeItemDto
{
    public string? Keyword { get; set; }
    public string? Status { get; set; }
    public string? Tag { get; set; }
    public string? ScopeJson { get; set; }
    public int PageIndex { get; set; } = 1;
    public int PageSize { get; set; } = 20;
}

/// <summary>
/// 分页响应DTO
/// </summary>
public class PagedResultDto<T>
{
    public List<T> Items { get; set; } = new();
    public int TotalCount { get; set; }
    public int PageIndex { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
}
