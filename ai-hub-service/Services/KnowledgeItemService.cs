using ai_hub_service.Data;
using ai_hub_service.DTOs;
using ai_hub_service.Models;
using Microsoft.EntityFrameworkCore;

namespace ai_hub_service.Services;

/// <summary>
/// 知识条目服务实现
/// </summary>
public class KnowledgeItemService : IKnowledgeItemService
{
    private readonly ApplicationDbContext _context;
    private readonly IIndexService _indexService;

    public KnowledgeItemService(ApplicationDbContext context, IIndexService indexService)
    {
        _context = context;
        _indexService = indexService;
    }

    /// <summary>
    /// 根据ID获取知识条目
    /// </summary>
    public async Task<KnowledgeItemDto?> GetByIdAsync(int id)
    {
        var item = await _context.KnowledgeItems
            .Include(k => k.Attachments)
            .FirstOrDefaultAsync(k => k.Id == id);

        if (item == null) return null;

        return MapToDto(item);
    }

    /// <summary>
    /// 搜索知识条目
    /// </summary>
    public async Task<PagedResultDto<KnowledgeItemDto>> SearchAsync(SearchKnowledgeItemDto searchDto)
    {
        try
        {
            // 验证分页参数
            if (searchDto.PageIndex < 1)
                searchDto.PageIndex = 1;
            if (searchDto.PageSize < 1)
                searchDto.PageSize = 20;
            if (searchDto.PageSize > 100)
                searchDto.PageSize = 100; // 限制最大页面大小

            var query = _context.KnowledgeItems
                .Include(k => k.Attachments)
                .AsQueryable();

            // 关键词搜索（title/question/solution）
            if (!string.IsNullOrWhiteSpace(searchDto.Keyword))
            {
                var keyword = searchDto.Keyword.Trim();
                query = query.Where(k =>
                    k.Title.Contains(keyword) ||
                    (k.QuestionText != null && k.QuestionText.Contains(keyword)) ||
                    (k.SolutionText != null && k.SolutionText.Contains(keyword)));
            }

            // 状态过滤
            if (!string.IsNullOrWhiteSpace(searchDto.Status))
            {
                query = query.Where(k => k.Status == searchDto.Status);
            }

            // 标签过滤
            if (!string.IsNullOrWhiteSpace(searchDto.Tag))
            {
                query = query.Where(k => k.Tags != null && k.Tags.Contains(searchDto.Tag));
            }

            // 适用范围过滤（简单匹配）
            if (!string.IsNullOrWhiteSpace(searchDto.ScopeJson))
            {
                query = query.Where(k => k.ScopeJson != null && k.ScopeJson.Contains(searchDto.ScopeJson));
            }

            // 获取总数
            var totalCount = await query.CountAsync();

            // 分页
            var items = await query
                .OrderByDescending(k => k.CreatedAt)
                .Skip((searchDto.PageIndex - 1) * searchDto.PageSize)
                .Take(searchDto.PageSize)
                .ToListAsync();

            return new PagedResultDto<KnowledgeItemDto>
            {
                Items = items.Select(MapToDto).ToList(),
                TotalCount = totalCount,
                PageIndex = searchDto.PageIndex,
                PageSize = searchDto.PageSize
            };
        }
        catch (Exception ex)
        {
            // 记录异常详情以便调试
            throw new Exception($"搜索知识条目时发生错误: {ex.Message}", ex);
        }
    }

    /// <summary>
    /// 创建知识条目
    /// </summary>
    public async Task<KnowledgeItemDto> CreateAsync(CreateKnowledgeItemDto createDto)
    {
        var item = new KnowledgeItem
        {
            Title = createDto.Title,
            QuestionText = createDto.QuestionText,
            CauseText = createDto.CauseText,
            SolutionText = createDto.SolutionText,
            ScopeJson = createDto.ScopeJson,
            Tags = createDto.Tags,
            Status = "draft",
            Version = 1,
            TenantId = createDto.TenantId,
            CreatedBy = createDto.CreatedBy,
            CreatedAt = DateTime.Now
        };

        _context.KnowledgeItems.Add(item);
        await _context.SaveChangesAsync();

        return MapToDto(item);
    }

    /// <summary>
    /// 更新知识条目
    /// </summary>
    public async Task<KnowledgeItemDto?> UpdateAsync(int id, UpdateKnowledgeItemDto updateDto)
    {
        var item = await _context.KnowledgeItems.FindAsync(id);
        if (item == null) return null;

        item.Title = updateDto.Title;
        item.QuestionText = updateDto.QuestionText;
        item.CauseText = updateDto.CauseText;
        item.SolutionText = updateDto.SolutionText;
        item.ScopeJson = updateDto.ScopeJson;
        item.Tags = updateDto.Tags;
        item.UpdatedAt = DateTime.Now;

        await _context.SaveChangesAsync();

        // 重新加载附件
        await _context.Entry(item).Collection(k => k.Attachments).LoadAsync();

        return MapToDto(item);
    }

    /// <summary>
    /// 删除知识条目
    /// </summary>
    public async Task<bool> DeleteAsync(int id)
    {
        var item = await _context.KnowledgeItems.FindAsync(id);
        if (item == null) return false;

        _context.KnowledgeItems.Remove(item);
        await _context.SaveChangesAsync();

        return true;
    }

    /// <summary>
    /// 发布知识条目
    /// </summary>
    public async Task<bool> PublishAsync(int id)
    {
        var item = await _context.KnowledgeItems
            .Include(k => k.Chunks)
            .FirstOrDefaultAsync(k => k.Id == id);

        if (item == null) return false;

        // 更新状态和发布时间
        item.Status = "published";
        item.PublishedAt = DateTime.Now;
        item.UpdatedAt = DateTime.Now;

        // 删除旧的chunks
        _context.KnowledgeChunks.RemoveRange(item.Chunks);

        // 生成新的chunks
        var chunks = GenerateChunks(item);
        _context.KnowledgeChunks.AddRange(chunks);

        await _context.SaveChangesAsync();

        // 调用向量化服务（占位）
        await _indexService.UpsertEmbeddingsAsync(chunks.Select(c => c.ChunkText).ToList());

        return true;
    }

    /// <summary>
    /// 生成知识块（将question/cause/solution合并后切分）
    /// </summary>
    private List<KnowledgeChunk> GenerateChunks(KnowledgeItem item)
    {
        var chunks = new List<KnowledgeChunk>();

        // 合并文本内容
        var fullText = string.Join("\n\n",
            new[] { item.QuestionText, item.CauseText, item.SolutionText }
                .Where(t => !string.IsNullOrWhiteSpace(t)));

        if (string.IsNullOrWhiteSpace(fullText))
            return chunks;

        // 简单切分：按段落切分，每段不超过1000字符
        const int maxChunkSize = 1000;
        var paragraphs = fullText.Split(new[] { "\n\n", "\n" }, StringSplitOptions.RemoveEmptyEntries);
        var currentChunk = new List<string>();
        var currentSize = 0;
        int chunkIndex = 0;

        foreach (var paragraph in paragraphs)
        {
            if (currentSize + paragraph.Length > maxChunkSize && currentChunk.Any())
            {
                // 保存当前chunk
                chunks.Add(new KnowledgeChunk
                {
                    KnowledgeItemId = item.Id,
                    ChunkText = string.Join("\n", currentChunk),
                    ChunkIndex = chunkIndex++,
                    CreatedAt = DateTime.Now
                });
                currentChunk.Clear();
                currentSize = 0;
            }

            currentChunk.Add(paragraph);
            currentSize += paragraph.Length;
        }

        // 保存最后一个chunk
        if (currentChunk.Any())
        {
            chunks.Add(new KnowledgeChunk
            {
                KnowledgeItemId = item.Id,
                ChunkText = string.Join("\n", currentChunk),
                ChunkIndex = chunkIndex,
                CreatedAt = DateTime.Now
            });
        }

        return chunks;
    }

    /// <summary>
    /// 映射实体到DTO
    /// </summary>
    private KnowledgeItemDto MapToDto(KnowledgeItem item)
    {
        if (item == null)
            throw new ArgumentNullException(nameof(item));

        return new KnowledgeItemDto
        {
            Id = item.Id,
            Title = item.Title ?? string.Empty,
            QuestionText = item.QuestionText,
            CauseText = item.CauseText,
            SolutionText = item.SolutionText,
            ScopeJson = item.ScopeJson,
            Tags = item.Tags,
            Status = item.Status ?? "draft",
            Version = item.Version,
            TenantId = item.TenantId,
            CreatedBy = item.CreatedBy,
            CreatedAt = item.CreatedAt,
            UpdatedAt = item.UpdatedAt,
            PublishedAt = item.PublishedAt,
            Attachments = item.Attachments?.Select(a => new AttachmentDto
            {
                Id = a.Id,
                KnowledgeItemId = a.KnowledgeItemId,
                FileName = a.FileName ?? string.Empty,
                FileUrl = a.FileUrl ?? string.Empty,
                FileType = a.FileType ?? string.Empty,
                FileSize = a.FileSize,
                CreatedAt = a.CreatedAt
            }).ToList() ?? new List<AttachmentDto>()
        };
    }
}
