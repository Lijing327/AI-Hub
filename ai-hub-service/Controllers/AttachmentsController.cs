using ai_hub_service.DTOs;
using ai_hub_service.Services;
using Microsoft.AspNetCore.Mvc;

namespace ai_hub_service.Controllers;

/// <summary>
/// 附件控制器
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class AttachmentsController : ControllerBase
{
    private readonly IAttachmentService _attachmentService;

    public AttachmentsController(IAttachmentService attachmentService)
    {
        _attachmentService = attachmentService;
    }

    /// <summary>
    /// 上传附件
    /// </summary>
    [HttpPost("upload")]
    public async Task<ActionResult<AttachmentDto>> Upload([FromForm] int knowledgeItemId, [FromForm] IFormFile file)
    {
        if (file == null || file.Length == 0)
            return BadRequest("文件不能为空");

        try
        {
            var attachment = await _attachmentService.UploadAsync(knowledgeItemId, file);
            return Ok(attachment);
        }
        catch (Exception ex)
        {
            return BadRequest(ex.Message);
        }
    }

    /// <summary>
    /// 删除附件
    /// </summary>
    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(int id)
    {
        var success = await _attachmentService.DeleteAsync(id);
        if (!success)
            return NotFound();

        return NoContent();
    }

    /// <summary>
    /// 获取知识条目的附件列表
    /// </summary>
    [HttpGet("knowledge-item/{knowledgeItemId}")]
    public async Task<ActionResult<List<AttachmentDto>>> GetByKnowledgeItemId(int knowledgeItemId)
    {
        var attachments = await _attachmentService.GetByKnowledgeItemIdAsync(knowledgeItemId);
        return Ok(attachments);
    }
}
