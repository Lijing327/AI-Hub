using ai_hub_service.Data;
using ai_hub_service.DTOs;
using ai_hub_service.Models;
using Microsoft.EntityFrameworkCore;

namespace ai_hub_service.Services;

/// <summary>
/// 附件服务实现（kb_asset）
/// </summary>
public class AssetService : IAssetService
{
    private readonly ApplicationDbContext _context;
    private readonly IConfiguration _configuration;
    private readonly IWebHostEnvironment _environment;

    public AssetService(
        ApplicationDbContext context,
        IConfiguration configuration,
        IWebHostEnvironment environment)
    {
        _context = context;
        _configuration = configuration;
        _environment = environment;
    }

    /// <summary>
    /// 上传附件
    /// </summary>
    public async Task<AssetDto> UploadAsync(int articleId, IFormFile file, string tenantId)
    {
        // 验证知识条目是否存在且属于当前租户
        var article = await _context.KnowledgeArticles
            .Where(a => a.Id == articleId && a.TenantId == tenantId && a.DeletedAt == null)
            .FirstOrDefaultAsync();
        if (article == null)
            throw new UnauthorizedAccessException($"知识条目 {articleId} 不存在或不属于当前租户");

        // 验证文件类型
        var allowedTypes = new[] { "image", "video", "pdf", "other" };
        var assetType = GetAssetType(file.ContentType, file.FileName);
        if (!allowedTypes.Contains(assetType))
            throw new ArgumentException($"不支持的文件类型: {assetType}");

        // 生成唯一文件名
        var fileName = $"{Guid.NewGuid()}_{file.FileName}";
        var localPath = _configuration["FileStorage:LocalPath"] ?? "wwwroot/uploads";
        var uploadPath = Path.Combine(_environment.ContentRootPath, localPath);
        
        // 确保目录存在
        if (!Directory.Exists(uploadPath))
            Directory.CreateDirectory(uploadPath);

        var filePath = Path.Combine(uploadPath, fileName);
        var baseUrl = _configuration["FileStorage:BaseUrl"] ?? "http://localhost:5000/uploads";
        var fileUrl = $"{baseUrl}/{fileName}";

        // 保存文件
        using (var stream = new FileStream(filePath, FileMode.Create))
        {
            await file.CopyToAsync(stream);
        }

        // 获取视频时长（如果是视频文件）
        int? duration = null;
        if (assetType == "video")
        {
            // TODO: 可以集成FFmpeg等库来获取视频时长
            // duration = await GetVideoDurationAsync(filePath);
        }

        // 保存到数据库
        var asset = new Asset
        {
            TenantId = tenantId, // 使用传入的 tenantId，确保一致性
            ArticleId = articleId,
            AssetType = assetType,
            FileName = file.FileName,
            Url = fileUrl, // 统一使用url字段（OSS/本地路径）
            Size = file.Length,
            Duration = duration,
            CreatedAt = DateTime.Now
        };

        _context.Assets.Add(asset);
        await _context.SaveChangesAsync();

        return new AssetDto
        {
            Id = asset.Id,
            TenantId = asset.TenantId,
            ArticleId = asset.ArticleId,
            AssetType = asset.AssetType,
            FileName = asset.FileName,
            Url = asset.Url,
            Size = asset.Size,
            Duration = asset.Duration,
            CreatedAt = asset.CreatedAt,
            DeletedAt = asset.DeletedAt
        };
    }

    /// <summary>
    /// 删除附件（软删除）
    /// </summary>
    public async Task<bool> DeleteAsync(int assetId, string tenantId)
    {
        var asset = await _context.Assets
            .Where(a => a.Id == assetId && a.TenantId == tenantId && a.DeletedAt == null)
            .FirstOrDefaultAsync();
        
        if (asset == null) return false;

        // 软删除：设置删除时间，不真正删除数据和文件
        asset.DeletedAt = DateTime.Now;
        await _context.SaveChangesAsync();

        return true;
    }

    /// <summary>
    /// 恢复已删除的附件
    /// </summary>
    public async Task<bool> RestoreAsync(int assetId, string tenantId)
    {
        var asset = await _context.Assets
            .Where(a => a.Id == assetId && a.TenantId == tenantId && a.DeletedAt != null)
            .FirstOrDefaultAsync();
        
        if (asset == null) return false;

        // 恢复：清除删除时间
        asset.DeletedAt = null;
        await _context.SaveChangesAsync();

        return true;
    }

    /// <summary>
    /// 根据知识条目ID获取附件列表
    /// </summary>
    public async Task<List<AssetDto>> GetByArticleIdAsync(int articleId, string tenantId)
    {
        // 先验证 article 属于当前租户
        var articleExists = await _context.KnowledgeArticles
            .AnyAsync(a => a.Id == articleId && a.TenantId == tenantId && a.DeletedAt == null);
        if (!articleExists)
            return new List<AssetDto>();

        var assets = await _context.Assets
            .Where(a => a.ArticleId == articleId && a.TenantId == tenantId && a.DeletedAt == null) // 只查询未删除的附件
            .OrderBy(a => a.CreatedAt)
            .ToListAsync();

        return assets.Select(a => new AssetDto
        {
            Id = a.Id,
            TenantId = a.TenantId,
            ArticleId = a.ArticleId,
            AssetType = a.AssetType,
            FileName = a.FileName,
            Url = a.Url,
            Size = a.Size,
            Duration = a.Duration,
            CreatedAt = a.CreatedAt,
            DeletedAt = a.DeletedAt
        }).ToList();
    }

    /// <summary>
    /// 创建附件记录（不实际上传文件，文件已在固定位置）
    /// </summary>
    public async Task<AssetDto> CreateAsync(ai_hub_service.DTOs.CreateAssetDto createDto, string tenantId)
    {
        // 验证知识条目是否存在且属于当前租户
        var article = await _context.KnowledgeArticles
            .Where(a => a.Id == createDto.ArticleId && a.TenantId == tenantId && a.DeletedAt == null)
            .FirstOrDefaultAsync();
        if (article == null)
            throw new UnauthorizedAccessException($"知识条目 {createDto.ArticleId} 不存在或不属于当前租户");

        // 验证资产类型
        var allowedTypes = new[] { "image", "video", "pdf", "other" };
        if (!allowedTypes.Contains(createDto.AssetType))
            throw new ArgumentException($"不支持的文件类型: {createDto.AssetType}");

        // 创建附件记录
        var asset = new Asset
        {
            TenantId = tenantId,
            ArticleId = createDto.ArticleId,
            AssetType = createDto.AssetType,
            FileName = createDto.FileName,
            Url = createDto.Url,
            Size = createDto.Size,
            Duration = createDto.Duration,
            CreatedAt = DateTime.Now
        };

        _context.Assets.Add(asset);
        await _context.SaveChangesAsync();

        return new AssetDto
        {
            Id = asset.Id,
            TenantId = asset.TenantId,
            ArticleId = asset.ArticleId,
            AssetType = asset.AssetType,
            FileName = asset.FileName,
            Url = asset.Url,
            Size = asset.Size,
            Duration = asset.Duration,
            CreatedAt = asset.CreatedAt,
            DeletedAt = asset.DeletedAt
        };
    }

    /// <summary>
    /// 根据ContentType和文件名判断资产类型
    /// </summary>
    private string GetAssetType(string contentType, string fileName)
    {
        var extension = Path.GetExtension(fileName).ToLower();
        
        // 图片类型
        if (contentType.StartsWith("image/") || 
            new[] { ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp" }.Contains(extension))
            return "image";

        // 视频类型
        if (contentType.StartsWith("video/") || 
            new[] { ".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv" }.Contains(extension))
            return "video";

        // PDF类型
        if (contentType == "application/pdf" || extension == ".pdf")
            return "pdf";

        return "other";
    }
}
