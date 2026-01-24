using ai_hub_service.Data;
using ai_hub_service.DTOs;
using ai_hub_service.Models;
using Microsoft.EntityFrameworkCore;
using System.Security.Cryptography;
using System.Text;

namespace ai_hub_service.Services;

/// <summary>
/// 知识主表服务实现
/// </summary>
public class KnowledgeArticleService : IKnowledgeArticleService
{
    private readonly ApplicationDbContext _context;
    private readonly IIndexService _indexService;

    public KnowledgeArticleService(ApplicationDbContext context, IIndexService indexService)
    {
        _context = context;
        _indexService = indexService;
    }

    /// <summary>
    /// 根据ID获取知识条目
    /// </summary>
    public async Task<KnowledgeArticleDto?> GetByIdAsync(int id, string tenantId)
    {
        var article = await _context.KnowledgeArticles
            .Where(a => a.Id == id && a.TenantId == tenantId && a.DeletedAt == null) // 只查询未删除的记录
            .FirstOrDefaultAsync();

        if (article == null) return null;

        // 手动加载未删除的附件
        await _context.Entry(article)
            .Collection(a => a.Assets)
            .Query()
            .Where(asset => asset.DeletedAt == null)
            .LoadAsync();

        if (article == null) return null;

        return MapToDto(article);
    }

    /// <summary>
    /// 搜索知识条目
    /// </summary>
    public async Task<PagedResultDto<KnowledgeArticleDto>> SearchAsync(SearchKnowledgeArticleDto searchDto, string tenantId)
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

            var query = _context.KnowledgeArticles
                .Where(a => a.TenantId == tenantId && a.DeletedAt == null) // 只查询未删除的记录
                .AsQueryable();

            // 关键词搜索（title/question/solution）
            if (!string.IsNullOrWhiteSpace(searchDto.Keyword))
            {
                var keyword = searchDto.Keyword.Trim();
                query = query.Where(a =>
                    a.Title.Contains(keyword) ||
                    (a.QuestionText != null && a.QuestionText.Contains(keyword)) ||
                    (a.SolutionText != null && a.SolutionText.Contains(keyword)));
            }

            // 状态过滤
            if (!string.IsNullOrWhiteSpace(searchDto.Status))
            {
                query = query.Where(a => a.Status == searchDto.Status);
            }

            // 标签过滤
            if (!string.IsNullOrWhiteSpace(searchDto.Tag))
            {
                query = query.Where(a => a.Tags != null && a.Tags.Contains(searchDto.Tag));
            }

            // 适用范围过滤（简单匹配）
            if (!string.IsNullOrWhiteSpace(searchDto.ScopeJson))
            {
                query = query.Where(a => a.ScopeJson != null && a.ScopeJson.Contains(searchDto.ScopeJson));
            }

            // 获取总数
            var totalCount = await query.CountAsync();

            // 分页
            var articles = await query
                .OrderByDescending(a => a.CreatedAt)
                .Skip((searchDto.PageIndex - 1) * searchDto.PageSize)
                .Take(searchDto.PageSize)
                .ToListAsync();

            // 为每个文章加载未删除的附件
            foreach (var article in articles)
            {
                await _context.Entry(article)
                    .Collection(a => a.Assets)
                    .Query()
                    .Where(asset => asset.DeletedAt == null)
                    .LoadAsync();
            }

            return new PagedResultDto<KnowledgeArticleDto>
            {
                Items = articles.Select(MapToDto).ToList(),
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
    public async Task<KnowledgeArticleDto> CreateAsync(CreateKnowledgeArticleDto createDto, string tenantId)
    {
        var article = new KnowledgeArticle
        {
            TenantId = tenantId, // 从请求头获取，不允许从DTO传入
            Title = createDto.Title,
            QuestionText = createDto.QuestionText,
            CauseText = createDto.CauseText,
            SolutionText = createDto.SolutionText,
            ScopeJson = createDto.ScopeJson,
            Tags = createDto.Tags,
            Status = "draft",
            Version = 1,
            CreatedBy = createDto.CreatedBy,
            CreatedAt = DateTime.Now
        };

        _context.KnowledgeArticles.Add(article);
        await _context.SaveChangesAsync();

        return MapToDto(article);
    }

    /// <summary>
    /// 更新知识条目
    /// </summary>
    public async Task<KnowledgeArticleDto?> UpdateAsync(int id, UpdateKnowledgeArticleDto updateDto, string tenantId)
    {
        var article = await _context.KnowledgeArticles
            .Where(a => a.Id == id && a.TenantId == tenantId && a.DeletedAt == null) // 只查询未删除的记录
            .FirstOrDefaultAsync();
        
        if (article == null) return null;

        article.Title = updateDto.Title;
        article.QuestionText = updateDto.QuestionText;
        article.CauseText = updateDto.CauseText;
        article.SolutionText = updateDto.SolutionText;
        article.ScopeJson = updateDto.ScopeJson;
        article.Tags = updateDto.Tags;
        article.UpdatedAt = DateTime.Now;

        await _context.SaveChangesAsync();

        // 重新加载附件
        await _context.Entry(article).Collection(a => a.Assets).LoadAsync();

        return MapToDto(article);
    }

    /// <summary>
    /// 删除知识条目（软删除）
    /// </summary>
    public async Task<bool> DeleteAsync(int id, string tenantId)
    {
        var article = await _context.KnowledgeArticles
            .Where(a => a.Id == id && a.TenantId == tenantId && a.DeletedAt == null)
            .FirstOrDefaultAsync();
        
        if (article == null) return false;

        // 软删除：设置删除时间，不真正删除数据
        article.DeletedAt = DateTime.Now;
        article.UpdatedAt = DateTime.Now;
        
        // 同时软删除关联的附件
        await _context.Entry(article).Collection(a => a.Assets).LoadAsync();
        foreach (var asset in article.Assets.Where(a => a.DeletedAt == null))
        {
            asset.DeletedAt = DateTime.Now;
        }

        await _context.SaveChangesAsync();

        return true;
    }

    /// <summary>
    /// 恢复已删除的知识条目
    /// </summary>
    public async Task<bool> RestoreAsync(int id, string tenantId)
    {
        var article = await _context.KnowledgeArticles
            .Where(a => a.Id == id && a.TenantId == tenantId && a.DeletedAt != null)
            .FirstOrDefaultAsync();
        
        if (article == null) return false;

        // 恢复：清除删除时间
        article.DeletedAt = null;
        article.UpdatedAt = DateTime.Now;

        // 恢复关联的附件
        await _context.Entry(article).Collection(a => a.Assets).LoadAsync();
        foreach (var asset in article.Assets.Where(a => a.DeletedAt != null))
        {
            asset.DeletedAt = null;
        }

        await _context.SaveChangesAsync();

        return true;
    }

    /// <summary>
    /// 发布知识条目
    /// </summary>
    public async Task<bool> PublishAsync(int id, string tenantId)
    {
        var article = await _context.KnowledgeArticles
            .Include(a => a.Chunks)
            .Where(a => a.Id == id && a.TenantId == tenantId && a.DeletedAt == null) // 只查询未删除的记录
            .FirstOrDefaultAsync();
        
        if (article == null) return false;

        // 更新状态和发布时间
        article.Status = "published";
        article.PublishedAt = DateTime.Now;
        article.UpdatedAt = DateTime.Now;

        // 删除旧的chunks
        _context.KnowledgeChunks.RemoveRange(article.Chunks);

        // 生成新的chunks（带hash和source_fields）
        var chunks = GenerateChunks(article);

        // 去重：仅同文章内去重（保留每个hash第一次出现的chunk）
        // 策略：同文章内chunk唯一，允许不同文章有相同chunk
        var seenHashes = new HashSet<string>();
        var uniqueChunks = new List<KnowledgeChunk>();

        foreach (var chunk in chunks)
        {
            if (chunk.Hash == null)
            {
                // hash 为 null 的 chunk 直接添加（理论上不会发生）
                uniqueChunks.Add(chunk);
            }
            else if (!seenHashes.Contains(chunk.Hash))
            {
                // 第一次出现的 hash，添加并记录
                seenHashes.Add(chunk.Hash);
                uniqueChunks.Add(chunk);
            }
            // 如果 hash 已存在，跳过（同文章内去重）
        }

        _context.KnowledgeChunks.AddRange(uniqueChunks);

        await _context.SaveChangesAsync();

        // 调用向量化服务（占位）
        await _indexService.UpsertEmbeddingsAsync(chunks.Select(c => c.ChunkText).ToList());

        return true;
    }

    /// <summary>
    /// 生成知识块（按标准顺序合并：知识ID、版本、标题、标签、适用范围、问题描述、原因分析、解决步骤）
    /// </summary>
    private List<KnowledgeChunk> GenerateChunks(KnowledgeArticle article)
    {
        var chunks = new List<KnowledgeChunk>();
        int chunkIndex = 0;

        // 按标准顺序构建完整文本
        var fullTextParts = new List<string>();

        // 0. 知识ID和版本（最前面，便于溯源）
        fullTextParts.Add($"【知识ID】\n{article.Id}");
        fullTextParts.Add($"【版本】\n{article.Version}");

        // 1. 标题
        if (!string.IsNullOrWhiteSpace(article.Title))
        {
            fullTextParts.Add($"【标题】\n{article.Title}");
        }

        // 2. 标签
        if (!string.IsNullOrWhiteSpace(article.Tags))
        {
            fullTextParts.Add($"【标签】\n{article.Tags}");
        }

        // 3. 适用范围
        if (!string.IsNullOrWhiteSpace(article.ScopeJson))
        {
            try
            {
                // 尝试格式化 JSON 为可读文本
                var scopeObj = System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, string>>(article.ScopeJson);
                if (scopeObj != null && scopeObj.Any())
                {
                    var scopeText = string.Join("、", scopeObj.Select(kv => $"{kv.Key}: {kv.Value}"));
                    fullTextParts.Add($"【适用范围】\n{scopeText}");
                }
                else
                {
                    fullTextParts.Add($"【适用范围】\n{article.ScopeJson}");
                }
            }
            catch
            {
                // JSON 解析失败，直接使用原始文本
                fullTextParts.Add($"【适用范围】\n{article.ScopeJson}");
            }
        }

        // 4. 问题描述
        if (!string.IsNullOrWhiteSpace(article.QuestionText))
        {
            fullTextParts.Add($"【问题描述】\n{article.QuestionText}");
        }

        // 5. 原因分析
        if (!string.IsNullOrWhiteSpace(article.CauseText))
        {
            fullTextParts.Add($"【原因分析】\n{article.CauseText}");
        }

        // 6. 解决步骤
        if (!string.IsNullOrWhiteSpace(article.SolutionText))
        {
            fullTextParts.Add($"【解决步骤】\n{article.SolutionText}");
        }

        // 合并为完整文本
        var fullText = string.Join("\n\n", fullTextParts);

        if (string.IsNullOrWhiteSpace(fullText))
        {
            return chunks; // 如果没有内容，返回空列表
        }

        // 按段落切分（保持结构）
        var paragraphs = fullText.Split(new[] { "\n\n", "\n" }, StringSplitOptions.RemoveEmptyEntries);
        const int maxChunkSize = 1000;
        var currentChunk = new List<string>();
        var currentSize = 0;
        string? currentSourceField = null; // 当前 chunk 的主要来源字段

        foreach (var paragraph in paragraphs)
        {
            // 判断段落来源
            string? sourceField = null;
            if (paragraph.Contains("【知识ID】"))
                sourceField = "metadata";
            else if (paragraph.Contains("【版本】"))
                sourceField = "metadata";
            else if (paragraph.Contains("【标题】"))
                sourceField = "title";
            else if (paragraph.Contains("【标签】"))
                sourceField = "tags";
            else if (paragraph.Contains("【适用范围】"))
                sourceField = "scope";
            else if (paragraph.Contains("【问题描述】"))
                sourceField = "question";
            else if (paragraph.Contains("【原因分析】"))
                sourceField = "cause";
            else if (paragraph.Contains("【解决步骤】"))
                sourceField = "solution";

            // 如果遇到新的来源字段，且当前 chunk 不为空，先保存当前 chunk
            if (sourceField != null && currentSourceField != null && currentChunk.Any() && sourceField != currentSourceField)
            {
                var chunkText = string.Join("\n", currentChunk);
                chunks.Add(CreateChunk(article, chunkText, chunkIndex++, currentSourceField));
                currentChunk.Clear();
                currentSize = 0;
            }

            // 如果当前 chunk 加上新段落会超过大小限制，先保存当前 chunk
            if (currentSize + paragraph.Length > maxChunkSize && currentChunk.Any())
            {
                var chunkText = string.Join("\n", currentChunk);
                chunks.Add(CreateChunk(article, chunkText, chunkIndex++, currentSourceField ?? "mixed"));
                currentChunk.Clear();
                currentSize = 0;
                currentSourceField = null;
            }

            currentChunk.Add(paragraph);
            currentSize += paragraph.Length;
            if (sourceField != null)
            {
                currentSourceField = sourceField;
            }
        }

        // 保存最后一个 chunk
        if (currentChunk.Any())
        {
            var chunkText = string.Join("\n", currentChunk);
            chunks.Add(CreateChunk(article, chunkText, chunkIndex++, currentSourceField ?? "mixed"));
        }

        return chunks;
    }

    /// <summary>
    /// 创建知识块（包含hash和source_fields）
    /// </summary>
    private KnowledgeChunk CreateChunk(KnowledgeArticle article, string chunkText, int chunkIndex, string sourceField)
    {
        // 计算hash（SHA256）
        var hash = ComputeHash(chunkText);

        return new KnowledgeChunk
        {
            TenantId = article.TenantId,
            ArticleId = article.Id,
            ChunkText = chunkText,
            ChunkIndex = chunkIndex,
            Hash = hash,
            SourceFields = sourceField,
            CreatedAt = DateTime.Now
        };
    }

    /// <summary>
    /// 计算文本的SHA256 hash（用于去重）
    /// </summary>
    private string ComputeHash(string text)
    {
        using (var sha256 = SHA256.Create())
        {
            var bytes = Encoding.UTF8.GetBytes(text);
            var hashBytes = sha256.ComputeHash(bytes);
            return BitConverter.ToString(hashBytes).Replace("-", "").ToLower();
        }
    }

    /// <summary>
    /// 映射实体到DTO
    /// </summary>
    private KnowledgeArticleDto MapToDto(KnowledgeArticle article)
    {
        if (article == null)
            throw new ArgumentNullException(nameof(article));

        return new KnowledgeArticleDto
        {
            Id = article.Id,
            TenantId = article.TenantId,
            Title = article.Title ?? string.Empty,
            QuestionText = article.QuestionText,
            CauseText = article.CauseText,
            SolutionText = article.SolutionText,
            ScopeJson = article.ScopeJson,
            Tags = article.Tags,
            Status = article.Status ?? "draft",
            Version = article.Version,
            CreatedBy = article.CreatedBy,
            CreatedAt = article.CreatedAt,
            UpdatedAt = article.UpdatedAt,
            PublishedAt = article.PublishedAt,
            DeletedAt = article.DeletedAt,
            Assets = article.Assets?.Where(a => a.DeletedAt == null).Select(a => new AssetDto
            {
                Id = a.Id,
                TenantId = a.TenantId,
                ArticleId = a.ArticleId,
                AssetType = a.AssetType ?? string.Empty,
                FileName = a.FileName ?? string.Empty,
                Url = a.Url ?? string.Empty,
                Size = a.Size,
                Duration = a.Duration,
                CreatedAt = a.CreatedAt,
                DeletedAt = a.DeletedAt
            }).ToList() ?? new List<AssetDto>()
        };
    }
}
