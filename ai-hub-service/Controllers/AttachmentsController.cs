using ai_hub_service.DTOs;
using ai_hub_service.Services;
using Microsoft.AspNetCore.Mvc;

namespace ai_hub_service.Controllers;

/// <summary>
/// 附件控制器（保持API路由兼容性）
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class AttachmentsController : BaseController
{
    private readonly IAssetService _assetService;

    public AttachmentsController(IAssetService assetService)
    {
        _assetService = assetService;
    }

    /// <summary>
    /// 上传附件
    /// </summary>
    [HttpPost("upload")]
    public async Task<ActionResult<AssetDto>> Upload([FromForm] int knowledgeItemId, [FromForm] IFormFile file)
    {
        if (file == null || file.Length == 0)
            return BadRequest("文件不能为空");

        try
        {
            var tenantId = GetTenantId();
            // 保持API兼容性：knowledgeItemId 实际对应 articleId
            var asset = await _assetService.UploadAsync(knowledgeItemId, file, tenantId);
            return Ok(asset);
        }
        catch (Exception ex)
        {
            return BadRequest(ex.Message);
        }
    }

    /// <summary>
    /// 删除附件（软删除）
    /// </summary>
    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(int id)
    {
        var tenantId = GetTenantId();
        var success = await _assetService.DeleteAsync(id, tenantId);
        if (!success)
            return NotFound();

        return Ok(new { message = "删除成功" });
    }

    /// <summary>
    /// 恢复已删除的附件
    /// </summary>
    [HttpPost("{id}/restore")]
    public async Task<ActionResult> Restore(int id)
    {
        var tenantId = GetTenantId();
        var success = await _assetService.RestoreAsync(id, tenantId);
        if (!success)
            return NotFound();

        return Ok(new { message = "恢复成功" });
    }

    /// <summary>
    /// 获取知识条目的附件列表
    /// </summary>
    [HttpGet("knowledge-item/{knowledgeItemId}")]
    public async Task<ActionResult<List<AssetDto>>> GetByKnowledgeItemId(int knowledgeItemId)
    {
        var tenantId = GetTenantId();
        // 保持API兼容性：knowledgeItemId 实际对应 articleId
        var assets = await _assetService.GetByArticleIdAsync(knowledgeItemId, tenantId);
        return Ok(assets);
    }
}
