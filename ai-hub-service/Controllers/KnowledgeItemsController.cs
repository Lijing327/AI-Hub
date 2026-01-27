using ai_hub_service.DTOs;
using ai_hub_service.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace ai_hub_service.Controllers;

/// <summary>
/// 知识条目控制器（保持API路由兼容性）
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class KnowledgeItemsController : BaseController
{
    private readonly IKnowledgeArticleService _knowledgeArticleService;
    private readonly ILogger<KnowledgeItemsController> _logger;

    public KnowledgeItemsController(
        IKnowledgeArticleService knowledgeArticleService,
        ILogger<KnowledgeItemsController> logger)
    {
        _knowledgeArticleService = knowledgeArticleService;
        _logger = logger;
    }

    /// <summary>
    /// 根据ID获取知识条目
    /// </summary>
    [HttpGet("{id}")]
    public async Task<ActionResult<KnowledgeArticleDto>> GetById(int id)
    {
        var tenantId = GetTenantId();
        var article = await _knowledgeArticleService.GetByIdAsync(id, tenantId);
        if (article == null)
            return NotFound();

        return Ok(article);
    }

    /// <summary>
    /// 搜索知识条目
    /// </summary>
    [HttpGet("search")]
    public async Task<ActionResult<PagedResultDto<KnowledgeArticleDto>>> Search([FromQuery] SearchKnowledgeArticleDto searchDto)
    {
        try
        {
            var tenantId = GetTenantId();
            _logger.LogInformation(
                "收到搜索请求 - TenantId: {TenantId}, Keyword: {Keyword}, Status: {Status}",
                tenantId, searchDto.Keyword, searchDto.Status);
            
            var result = await _knowledgeArticleService.SearchAsync(searchDto, tenantId);
            
            _logger.LogInformation(
                "搜索完成 - 找到 {Count} 条记录",
                result.TotalCount);
            
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, 
                "搜索知识条目时发生错误 - Keyword: {Keyword}, Status: {Status}",
                searchDto.Keyword, searchDto.Status);
            
            // 记录异常并返回500错误
            return StatusCode(500, new { 
                error = "搜索知识条目时发生错误", 
                message = ex.Message,
                innerException = ex.InnerException?.Message
            });
        }
    }

    /// <summary>
    /// 创建知识条目
    /// </summary>
    [HttpPost]
    public async Task<ActionResult<KnowledgeArticleDto>> Create([FromBody] CreateKnowledgeArticleDto createDto)
    {
        var tenantId = GetTenantId();
        var article = await _knowledgeArticleService.CreateAsync(createDto, tenantId);
        return CreatedAtAction(nameof(GetById), new { id = article.Id }, article);
    }

    /// <summary>
    /// 更新知识条目
    /// </summary>
    [HttpPut("{id}")]
    public async Task<ActionResult<KnowledgeArticleDto>> Update(int id, [FromBody] UpdateKnowledgeArticleDto updateDto)
    {
        var tenantId = GetTenantId();
        var article = await _knowledgeArticleService.UpdateAsync(id, updateDto, tenantId);
        if (article == null)
            return NotFound();

        return Ok(article);
    }

    /// <summary>
    /// 删除知识条目（软删除）
    /// </summary>
    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(int id)
    {
        var tenantId = GetTenantId();
        var success = await _knowledgeArticleService.DeleteAsync(id, tenantId);
        if (!success)
            return NotFound();

        return Ok(new { message = "删除成功" });
    }

    /// <summary>
    /// 恢复已删除的知识条目
    /// </summary>
    [HttpPost("{id}/restore")]
    public async Task<ActionResult> Restore(int id)
    {
        var tenantId = GetTenantId();
        var success = await _knowledgeArticleService.RestoreAsync(id, tenantId);
        if (!success)
            return NotFound();

        return Ok(new { message = "恢复成功" });
    }

    /// <summary>
    /// 发布知识条目
    /// </summary>
    [HttpPost("{id}/publish")]
    public async Task<ActionResult> Publish(int id)
    {
        var tenantId = GetTenantId();
        var success = await _knowledgeArticleService.PublishAsync(id, tenantId);
        if (!success)
            return NotFound();

        return Ok(new { message = "发布成功" });
    }
}
