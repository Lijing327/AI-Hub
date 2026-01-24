using ai_hub_service.DTOs;
using ai_hub_service.Services;
using Microsoft.AspNetCore.Mvc;

namespace ai_hub_service.Controllers;

/// <summary>
/// 知识条目控制器（保持API路由兼容性）
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class KnowledgeItemsController : ControllerBase
{
    private readonly IKnowledgeArticleService _knowledgeArticleService;

    public KnowledgeItemsController(IKnowledgeArticleService knowledgeArticleService)
    {
        _knowledgeArticleService = knowledgeArticleService;
    }

    /// <summary>
    /// 根据ID获取知识条目
    /// </summary>
    [HttpGet("{id}")]
    public async Task<ActionResult<KnowledgeArticleDto>> GetById(int id)
    {
        var article = await _knowledgeArticleService.GetByIdAsync(id);
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
            var result = await _knowledgeArticleService.SearchAsync(searchDto);
            return Ok(result);
        }
        catch (Exception ex)
        {
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
        var article = await _knowledgeArticleService.CreateAsync(createDto);
        return CreatedAtAction(nameof(GetById), new { id = article.Id }, article);
    }

    /// <summary>
    /// 更新知识条目
    /// </summary>
    [HttpPut("{id}")]
    public async Task<ActionResult<KnowledgeArticleDto>> Update(int id, [FromBody] UpdateKnowledgeArticleDto updateDto)
    {
        var article = await _knowledgeArticleService.UpdateAsync(id, updateDto);
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
        var success = await _knowledgeArticleService.DeleteAsync(id);
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
        var success = await _knowledgeArticleService.RestoreAsync(id);
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
        var success = await _knowledgeArticleService.PublishAsync(id);
        if (!success)
            return NotFound();

        return Ok(new { message = "发布成功" });
    }
}
