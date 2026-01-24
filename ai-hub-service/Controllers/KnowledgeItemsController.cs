using ai_hub_service.DTOs;
using ai_hub_service.Services;
using Microsoft.AspNetCore.Mvc;

namespace ai_hub_service.Controllers;

/// <summary>
/// 知识条目控制器
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class KnowledgeItemsController : ControllerBase
{
    private readonly IKnowledgeItemService _knowledgeItemService;

    public KnowledgeItemsController(IKnowledgeItemService knowledgeItemService)
    {
        _knowledgeItemService = knowledgeItemService;
    }

    /// <summary>
    /// 根据ID获取知识条目
    /// </summary>
    [HttpGet("{id}")]
    public async Task<ActionResult<KnowledgeItemDto>> GetById(int id)
    {
        var item = await _knowledgeItemService.GetByIdAsync(id);
        if (item == null)
            return NotFound();

        return Ok(item);
    }

    /// <summary>
    /// 搜索知识条目
    /// </summary>
    [HttpGet("search")]
    public async Task<ActionResult<PagedResultDto<KnowledgeItemDto>>> Search([FromQuery] SearchKnowledgeItemDto searchDto)
    {
        try
        {
            var result = await _knowledgeItemService.SearchAsync(searchDto);
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
    public async Task<ActionResult<KnowledgeItemDto>> Create([FromBody] CreateKnowledgeItemDto createDto)
    {
        var item = await _knowledgeItemService.CreateAsync(createDto);
        return CreatedAtAction(nameof(GetById), new { id = item.Id }, item);
    }

    /// <summary>
    /// 更新知识条目
    /// </summary>
    [HttpPut("{id}")]
    public async Task<ActionResult<KnowledgeItemDto>> Update(int id, [FromBody] UpdateKnowledgeItemDto updateDto)
    {
        var item = await _knowledgeItemService.UpdateAsync(id, updateDto);
        if (item == null)
            return NotFound();

        return Ok(item);
    }

    /// <summary>
    /// 删除知识条目
    /// </summary>
    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(int id)
    {
        var success = await _knowledgeItemService.DeleteAsync(id);
        if (!success)
            return NotFound();

        return NoContent();
    }

    /// <summary>
    /// 发布知识条目
    /// </summary>
    [HttpPost("{id}/publish")]
    public async Task<ActionResult> Publish(int id)
    {
        var success = await _knowledgeItemService.PublishAsync(id);
        if (!success)
            return NotFound();

        return Ok(new { message = "发布成功" });
    }
}
