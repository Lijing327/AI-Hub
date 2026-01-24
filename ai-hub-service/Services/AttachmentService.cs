using ai_hub_service.Data;
using ai_hub_service.DTOs;
using ai_hub_service.Models;
using Microsoft.EntityFrameworkCore;

namespace ai_hub_service.Services;

/// <summary>
/// 附件服务实现
/// </summary>
public class AttachmentService : IAttachmentService
{
    private readonly ApplicationDbContext _context;
    private readonly IConfiguration _configuration;
    private readonly IWebHostEnvironment _environment;

    public AttachmentService(
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
    public async Task<AttachmentDto> UploadAsync(int knowledgeItemId, IFormFile file)
    {
        // 验证知识条目是否存在
        var knowledgeItem = await _context.KnowledgeItems.FindAsync(knowledgeItemId);
        if (knowledgeItem == null)
            throw new ArgumentException($"知识条目 {knowledgeItemId} 不存在");

        // 验证文件类型
        var allowedTypes = new[] { "image", "video", "pdf" };
        var fileType = GetFileType(file.ContentType, file.FileName);
        if (!allowedTypes.Contains(fileType))
            throw new ArgumentException($"不支持的文件类型: {fileType}");

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

        // 保存到数据库
        var attachment = new Attachment
        {
            KnowledgeItemId = knowledgeItemId,
            FileName = file.FileName,
            FilePath = filePath,
            FileUrl = fileUrl,
            FileType = fileType,
            FileSize = file.Length,
            CreatedAt = DateTime.Now
        };

        _context.Attachments.Add(attachment);
        await _context.SaveChangesAsync();

        return new AttachmentDto
        {
            Id = attachment.Id,
            KnowledgeItemId = attachment.KnowledgeItemId,
            FileName = attachment.FileName,
            FileUrl = attachment.FileUrl,
            FileType = attachment.FileType,
            FileSize = attachment.FileSize,
            CreatedAt = attachment.CreatedAt
        };
    }

    /// <summary>
    /// 删除附件
    /// </summary>
    public async Task<bool> DeleteAsync(int attachmentId)
    {
        var attachment = await _context.Attachments.FindAsync(attachmentId);
        if (attachment == null) return false;

        // 删除物理文件
        if (File.Exists(attachment.FilePath))
        {
            File.Delete(attachment.FilePath);
        }

        // 删除数据库记录
        _context.Attachments.Remove(attachment);
        await _context.SaveChangesAsync();

        return true;
    }

    /// <summary>
    /// 根据知识条目ID获取附件列表
    /// </summary>
    public async Task<List<AttachmentDto>> GetByKnowledgeItemIdAsync(int knowledgeItemId)
    {
        var attachments = await _context.Attachments
            .Where(a => a.KnowledgeItemId == knowledgeItemId)
            .OrderBy(a => a.CreatedAt)
            .ToListAsync();

        return attachments.Select(a => new AttachmentDto
        {
            Id = a.Id,
            KnowledgeItemId = a.KnowledgeItemId,
            FileName = a.FileName,
            FileUrl = a.FileUrl,
            FileType = a.FileType,
            FileSize = a.FileSize,
            CreatedAt = a.CreatedAt
        }).ToList();
    }

    /// <summary>
    /// 根据ContentType和文件名判断文件类型
    /// </summary>
    private string GetFileType(string contentType, string fileName)
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

        return "unknown";
    }
}
