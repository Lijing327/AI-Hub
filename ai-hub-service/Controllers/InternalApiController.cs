using ai_hub_service.DTOs;
using ai_hub_service.Services;
using Microsoft.AspNetCore.Mvc;

namespace ai_hub_service.Controllers;

/// <summary>
/// 内部 API 控制器（供 Python 服务调用）
/// </summary>
[ApiController]
[Route("api/ai/kb/articles")]
public class InternalApiController : BaseController
{
    private readonly IKnowledgeArticleService _knowledgeArticleService;
    private readonly IAssetService _assetService;

    public InternalApiController(
        IKnowledgeArticleService knowledgeArticleService,
        IAssetService assetService)
    {
        _knowledgeArticleService = knowledgeArticleService;
        _assetService = assetService;
    }

    /// <summary>
    /// 批量创建知识条目（草稿状态）
    /// </summary>
    [HttpPost("batch")]
    public async Task<ActionResult<BatchCreateArticlesResponseDto>> BatchCreate(
        [FromBody] BatchCreateArticlesRequestDto request)
    {
        if (request.Articles == null || request.Articles.Count == 0)
        {
            return BadRequest("Articles 列表不能为空");
        }

        var tenantId = GetTenantId();
        var response = new BatchCreateArticlesResponseDto();

        for (int i = 0; i < request.Articles.Count; i++)
        {
            var articleDto = request.Articles[i];
            var resultItem = new BatchCreateResultItemDto { Index = i };

            try
            {
                // 验证必需字段
                if (string.IsNullOrWhiteSpace(articleDto.Title))
                {
                    resultItem.Success = false;
                    resultItem.Error = "Title 不能为空";
                    response.FailureCount++;
                }
                else
                {
                    var article = await _knowledgeArticleService.CreateAsync(articleDto, tenantId);
                    resultItem.Success = true;
                    resultItem.ArticleId = article.Id;
                    response.SuccessCount++;
                }
            }
            catch (Exception ex)
            {
                resultItem.Success = false;
                resultItem.Error = ex.Message;
                response.FailureCount++;
            }

            response.Results.Add(resultItem);
        }

        return Ok(response);
    }

    /// <summary>
    /// 批量发布知识条目
    /// </summary>
    [HttpPost("publish/batch")]
    public async Task<ActionResult<BatchPublishArticlesResponseDto>> BatchPublish(
        [FromBody] BatchPublishArticlesRequestDto request)
    {
        if (request.ArticleIds == null || request.ArticleIds.Count == 0)
        {
            return BadRequest("ArticleIds 列表不能为空");
        }

        var tenantId = GetTenantId();
        var response = new BatchPublishArticlesResponseDto();

        foreach (var articleId in request.ArticleIds)
        {
            var resultItem = new BatchPublishResultItemDto { ArticleId = articleId };

            try
            {
                var success = await _knowledgeArticleService.PublishAsync(articleId, tenantId);
                resultItem.Success = success;
                if (success)
                {
                    response.SuccessCount++;
                }
                else
                {
                    resultItem.Error = "未找到或不属于当前租户";
                    response.FailureCount++;
                }
            }
            catch (Exception ex)
            {
                resultItem.Success = false;
                resultItem.Error = ex.Message;
                response.FailureCount++;
            }

            response.Results.Add(resultItem);
        }

        return Ok(response);
    }

    /// <summary>
    /// 批量创建附件记录（文件已在固定位置，只创建数据库记录）
    /// </summary>
    [HttpPost("assets/batch")]
    public async Task<ActionResult<BatchCreateAssetsResponseDto>> BatchCreateAssets(
        [FromBody] BatchCreateAssetsRequestDto request)
    {
        if (request.Assets == null || request.Assets.Count == 0)
        {
            return BadRequest("Assets 列表不能为空");
        }

        var tenantId = GetTenantId();
        var response = new BatchCreateAssetsResponseDto();

        for (int i = 0; i < request.Assets.Count; i++)
        {
            var assetDto = request.Assets[i];
            var resultItem = new BatchCreateAssetResultItemDto { Index = i };

            try
            {
                // 验证必需字段
                if (assetDto.ArticleId <= 0)
                {
                    resultItem.Success = false;
                    resultItem.Error = "ArticleId 必须大于 0";
                    response.FailureCount++;
                }
                else if (string.IsNullOrWhiteSpace(assetDto.Url))
                {
                    resultItem.Success = false;
                    resultItem.Error = "Url 不能为空";
                    response.FailureCount++;
                }
                else
                {
                    var asset = await _assetService.CreateAsync(assetDto, tenantId);
                    resultItem.Success = true;
                    resultItem.AssetId = asset.Id;
                    response.SuccessCount++;
                }
            }
            catch (Exception ex)
            {
                resultItem.Success = false;
                resultItem.Error = ex.Message;
                response.FailureCount++;
            }

            response.Results.Add(resultItem);
        }

        return Ok(response);
    }
}
