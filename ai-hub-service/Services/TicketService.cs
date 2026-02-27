using System.Text.Json;
using AiHub.DTOs;
using AiHub.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using ai_hub_service.Data;
using ai_hub_service.DTOs;
using ai_hub_service.Models;

namespace AiHub.Services;

/// <summary>
/// 工单服务实现
/// </summary>
public class TicketService : ITicketService
{
    private readonly ApplicationDbContext _context;
    private readonly ILogger<TicketService> _logger;
    private readonly IConfiguration _configuration;
    private readonly IHttpClientFactory _httpClientFactory;

    public TicketService(
        ApplicationDbContext context,
        ILogger<TicketService> logger,
        IConfiguration configuration,
        IHttpClientFactory httpClientFactory)
    {
        _context = context;
        _logger = logger;
        _configuration = configuration;
        _httpClientFactory = httpClientFactory;
    }

    /// <summary>
    /// 生成工单号（按日期 + 序号）
    /// </summary>
    private async Task<string> GenerateTicketNoAsync()
    {
        var today = DateTime.Now;
        var datePrefix = today.ToString("yyyyMMdd");

        // 查询今天最大的序号
        var maxTicket = await _context.Tickets
            .Where(t => t.TicketNo.StartsWith(datePrefix))
            .OrderByDescending(t => t.TicketNo)
            .FirstOrDefaultAsync();

        int nextSequence = 1;
        if (maxTicket != null && !string.IsNullOrEmpty(maxTicket.TicketNo) && maxTicket.TicketNo.Length == 12)
        {
            if (int.TryParse(maxTicket.TicketNo.Substring(8), out int seq))
            {
                nextSequence = seq + 1;
            }
        }

        return $"{datePrefix}{nextSequence:D4}";
    }

    /// <summary>
    /// 创建工单日志记录
    /// </summary>
    private async Task<TicketLog> CreateLogAsync(Guid ticketId, string action, string? content,
        string operatorId, string? operatorName, string? nextStatus)
    {
        var log = new TicketLog
        {
            TicketId = ticketId,
            Action = action,
            Content = content,
            OperatorId = operatorId,
            OperatorName = operatorName,
            NextStatus = nextStatus,
            CreatedAt = DateTime.Now
        };

        _context.TicketLogs.Add(log);
        await _context.SaveChangesAsync();

        return log;
    }

    /// <summary>
    /// 映射实体到列表 DTO
    /// </summary>
    private TicketListDto MapToListDto(Ticket ticket)
    {
        return new TicketListDto
        {
            TicketId = ticket.TicketId,
            TicketNo = ticket.TicketNo,
            Title = ticket.Title,
            Status = ticket.Status,
            Priority = ticket.Priority,
            Source = ticket.Source,
            DeviceMn = ticket.DeviceMn,
            AssigneeName = ticket.AssigneeName,
            CreatedBy = ticket.CreatedBy,
            CreatedAt = ticket.CreatedAt
        };
    }

    /// <summary>
    /// 映射实体到详情 DTO
    /// </summary>
    private async Task<TicketDetailDto> MapToDetailDtoAsync(Ticket ticket)
    {
        var logs = await _context.TicketLogs
            .Where(l => l.TicketId == ticket.TicketId)
            .OrderBy(l => l.CreatedAt)
            .ToListAsync();

        return new TicketDetailDto
        {
            TicketId = ticket.TicketId,
            TicketNo = ticket.TicketNo,
            TenantId = ticket.TenantId,
            Title = ticket.Title,
            Description = ticket.Description,
            Status = ticket.Status,
            Priority = ticket.Priority,
            Source = ticket.Source,
            CustomerId = ticket.CustomerId,
            DeviceId = ticket.DeviceId,
            DeviceMn = ticket.DeviceMn,
            SessionId = ticket.SessionId,
            TriggerMessageId = ticket.TriggerMessageId,
            AssigneeId = ticket.AssigneeId,
            AssigneeName = ticket.AssigneeName,
            CreatedBy = ticket.CreatedBy,
            CreatedAt = ticket.CreatedAt,
            UpdatedAt = ticket.UpdatedAt,
            ClosedAt = ticket.ClosedAt,
            FinalSolutionSummary = ticket.FinalSolutionSummary,
            Meta = ticket.Meta != null ? new AiHub.DTOs.TicketMeta
            {
                IssueCategory = ticket.Meta.IssueCategory,
                AlarmCode = ticket.Meta.AlarmCode,
                CitedDocs = ticket.Meta.CitedDocs
            } : null,
            KbArticleId = ticket.KbArticleId,
            Logs = logs.Select(l => new TicketLogDto
            {
                LogId = l.LogId,
                TicketId = l.TicketId,
                Action = l.Action,
                Content = l.Content,
                OperatorId = l.OperatorId,
                OperatorName = l.OperatorName,
                NextStatus = l.NextStatus,
                CreatedAt = l.CreatedAt
            }).ToList()
        };
    }

    public async Task<TicketDetailDto> CreateAsync(CreateTicketRequest request, string userId, string tenantId)
    {
        var ticketNo = await GenerateTicketNoAsync();

        var ticket = new Ticket
        {
            TicketId = Guid.NewGuid(),
            TenantId = tenantId,
            TicketNo = ticketNo,
            Title = request.Title,
            Description = request.Description,
            Status = TicketStatus.Pending,
            Priority = request.Priority ?? TicketPriority.Medium,
            Source = request.Source ?? TicketSource.Manual,
            CustomerId = request.CustomerId,
            DeviceId = request.DeviceId,
            DeviceMn = request.DeviceMn,
            SessionId = request.SessionId,
            TriggerMessageId = request.TriggerMessageId,
            CreatedBy = userId,
            MetaJson = request.Meta != null ? System.Text.Json.JsonSerializer.Serialize(request.Meta) : null
        };

        _context.Tickets.Add(ticket);
        await _context.SaveChangesAsync();

        // 记录创建日志
        await CreateLogAsync(
            ticket.TicketId,
            TicketLogAction.Create,
            $"创建工单：{request.Title}",
            userId,
            null,
            TicketStatus.Pending);

        _logger.LogInformation("工单已创建：{TicketNo}, {Title}", ticket.TicketNo, ticket.Title);

        return await MapToDetailDtoAsync(ticket);
    }

    public async Task<PagedResultDto<TicketListDto>> ListAsync(TicketQueryRequest query, string userId, string tenantId, bool isStaff)
    {
        var queryable = _context.Tickets.AsQueryable();

        // 租户隔离
        queryable = queryable.Where(t => t.TenantId == tenantId);

        // 非工程师只能看自己的工单
        if (!isStaff)
        {
            queryable = queryable.Where(t => t.CreatedBy == userId || t.AssigneeId == userId);
        }

        // 状态过滤
        if (!string.IsNullOrWhiteSpace(query.Status))
        {
            queryable = queryable.Where(t => t.Status == query.Status);
        }

        // 优先级过滤
        if (!string.IsNullOrWhiteSpace(query.Priority))
        {
            queryable = queryable.Where(t => t.Priority == query.Priority);
        }

        // 设备 MN 号过滤
        if (!string.IsNullOrWhiteSpace(query.DeviceMn))
        {
            queryable = queryable.Where(t => t.DeviceMn == query.DeviceMn);
        }

        // 分配人过滤
        if (!string.IsNullOrWhiteSpace(query.AssigneeId))
        {
            queryable = queryable.Where(t => t.AssigneeId == query.AssigneeId);
        }

        // 关键词搜索
        if (!string.IsNullOrWhiteSpace(query.Keyword))
        {
            var keyword = query.Keyword.Trim();
            queryable = queryable.Where(t =>
                EF.Functions.Like(t.Title, $"%{keyword}%") ||
                (t.Description != null && EF.Functions.Like(t.Description, $"%{keyword}%")));
        }

        // 获取总数
        var totalCount = await queryable.CountAsync();

        // 分页排序（按创建时间倒序）
        var items = await queryable
            .OrderByDescending(t => t.CreatedAt)
            .Skip((query.PageIndex - 1) * query.PageSize)
            .Take(query.PageSize)
            .ToListAsync();

        return new PagedResultDto<TicketListDto>
        {
            Items = items.Select(MapToListDto).ToList(),
            TotalCount = totalCount,
            PageIndex = query.PageIndex,
            PageSize = query.PageSize
        };
    }

    public async Task<TicketDetailDto?> GetByIdAsync(Guid ticketId, string userId, string tenantId, bool isStaff)
    {
        var ticket = await _context.Tickets
            .FirstOrDefaultAsync(t => t.TicketId == ticketId && t.TenantId == tenantId);

        if (ticket == null) return null;

        // 非工程师只能看自己创建或分配的工单
        if (!isStaff && ticket.CreatedBy != userId && ticket.AssigneeId != userId)
        {
            return null;
        }

        return await MapToDetailDtoAsync(ticket);
    }

    public async Task<TicketDetailDto?> UpdateAsync(Guid ticketId, UpdateTicketRequest request, string userId, string tenantId)
    {
        var ticket = await _context.Tickets
            .FirstOrDefaultAsync(t => t.TicketId == ticketId && t.TenantId == tenantId);

        if (ticket == null) return null;

        if (request.Title != null) ticket.Title = request.Title;
        if (request.Description != null) ticket.Description = request.Description;
        if (request.Priority != null) ticket.Priority = request.Priority;
        if (request.AssigneeId != null) ticket.AssigneeId = request.AssigneeId;
        if (request.AssigneeName != null) ticket.AssigneeName = request.AssigneeName;
        if (request.FinalSolutionSummary != null) ticket.FinalSolutionSummary = request.FinalSolutionSummary;
        if (request.Meta != null) ticket.Meta = new Ticket.TicketMeta
        {
            IssueCategory = request.Meta.IssueCategory,
            AlarmCode = request.Meta.AlarmCode,
            CitedDocs = request.Meta.CitedDocs ?? new List<string>()
        };

        ticket.UpdatedAt = DateTime.Now;

        await _context.SaveChangesAsync();

        return await MapToDetailDtoAsync(ticket);
    }

    public async Task<TicketDetailDto?> StartAsync(Guid ticketId, StartTicketRequest? request, string userId, string tenantId)
    {
        var ticket = await _context.Tickets
            .FirstOrDefaultAsync(t => t.TicketId == ticketId && t.TenantId == tenantId);

        if (ticket == null) return null;

        if (ticket.Status != TicketStatus.Pending)
        {
            throw new InvalidOperationException($"工单当前状态为 {ticket.Status}，无法开始处理");
        }

        ticket.Status = TicketStatus.Processing;
        if (request?.AssigneeId != null) ticket.AssigneeId = request.AssigneeId;
        if (request?.AssigneeName != null) ticket.AssigneeName = request.AssigneeName;
        ticket.UpdatedAt = DateTime.Now;

        await _context.SaveChangesAsync();

        // 记录开始处理日志
        var note = request?.Note ?? "工程师开始处理此工单";
        await CreateLogAsync(
            ticketId,
            TicketLogAction.Start,
            note,
            userId,
            null,
            TicketStatus.Processing);

        _logger.LogInformation("工单已开始处理：{TicketNo}", ticket.TicketNo);

        return await MapToDetailDtoAsync(ticket);
    }

    public async Task<TicketDetailDto?> ResolveAsync(Guid ticketId, ResolveTicketRequest request, string userId, string tenantId)
    {
        var ticket = await _context.Tickets
            .FirstOrDefaultAsync(t => t.TicketId == ticketId && t.TenantId == tenantId);

        if (ticket == null) return null;

        if (ticket.Status != TicketStatus.Processing)
        {
            throw new InvalidOperationException($"工单当前状态为 {ticket.Status}，无法标记为已解决");
        }

        if (string.IsNullOrWhiteSpace(request.FinalSolutionSummary))
        {
            throw new ArgumentException("最终解决方案摘要不能为空");
        }

        ticket.Status = TicketStatus.Resolved;
        ticket.FinalSolutionSummary = request.FinalSolutionSummary;
        ticket.UpdatedAt = DateTime.Now;

        await _context.SaveChangesAsync();

        // 记录解决日志
        var note = request.Note ?? "工程师已标记工单为已解决";
        await CreateLogAsync(
            ticketId,
            TicketLogAction.Resolve,
            note,
            userId,
            null,
            TicketStatus.Resolved);

        _logger.LogInformation("工单已解决：{TicketNo}", ticket.TicketNo);

        return await MapToDetailDtoAsync(ticket);
    }

    public async Task<TicketDetailDto?> CloseAsync(Guid ticketId, CloseTicketRequest? request, string userId, string tenantId)
    {
        var ticket = await _context.Tickets
            .FirstOrDefaultAsync(t => t.TicketId == ticketId && t.TenantId == tenantId);

        if (ticket == null) return null;

        if (ticket.Status == TicketStatus.Closed)
        {
            throw new InvalidOperationException("工单已是关闭状态");
        }

        ticket.Status = TicketStatus.Closed;
        ticket.ClosedAt = DateTime.Now;
        ticket.UpdatedAt = DateTime.Now;

        await _context.SaveChangesAsync();

        // 记录关闭日志
        var note = request?.Note ?? "工单已关闭";
        await CreateLogAsync(
            ticketId,
            TicketLogAction.Close,
            note,
            userId,
            null,
            TicketStatus.Closed);

        _logger.LogInformation("工单已关闭：{TicketNo}", ticket.TicketNo);

        return await MapToDetailDtoAsync(ticket);
    }

    public async Task<TicketLogDto> AddLogAsync(Guid ticketId, CreateTicketLogRequest request, string userId, string tenantId)
    {
        var ticket = await _context.Tickets
            .FirstOrDefaultAsync(t => t.TicketId == ticketId && t.TenantId == tenantId);

        if (ticket == null)
        {
            throw new KeyNotFoundException("工单不存在");
        }

        var log = await CreateLogAsync(
            ticketId,
            TicketLogAction.Comment,
            request.Content,
            userId,
            request.OperatorName,
            null);

        return new TicketLogDto
        {
            LogId = log.LogId,
            TicketId = log.TicketId,
            Action = log.Action,
            Content = log.Content,
            OperatorId = log.OperatorId,
            OperatorName = log.OperatorName,
            NextStatus = log.NextStatus,
            CreatedAt = log.CreatedAt
        };
    }

    public async Task<List<TicketLogDto>> GetLogsAsync(Guid ticketId, string userId, string tenantId)
    {
        var ticket = await _context.Tickets
            .FirstOrDefaultAsync(t => t.TicketId == ticketId && t.TenantId == tenantId);

        if (ticket == null)
        {
            throw new KeyNotFoundException("工单不存在");
        }

        var logs = await _context.TicketLogs
            .Where(l => l.TicketId == ticketId)
            .OrderBy(l => l.CreatedAt)
            .ToListAsync();

        return logs.Select(l => new TicketLogDto
        {
            LogId = l.LogId,
            TicketId = l.TicketId,
            Action = l.Action,
            Content = l.Content,
            OperatorId = l.OperatorId,
            OperatorName = l.OperatorName,
            NextStatus = l.NextStatus,
            CreatedAt = l.CreatedAt
        }).ToList();
    }

    /// <summary>
    /// 将工单转换为知识库文章
    /// </summary>
    public async Task<(int articleId, string message, bool vectorSuccess)> ConvertToKbAsync(
        Guid ticketId, string userId, string tenantId, bool triggerVectorIndex = true)
    {
        var ticket = await _context.Tickets
            .FirstOrDefaultAsync(t => t.TicketId == ticketId && t.TenantId == tenantId);

        if (ticket == null)
        {
            throw new KeyNotFoundException("工单不存在");
        }

        if (ticket.KbArticleId.HasValue)
        {
            throw new InvalidOperationException("该工单已转换为知识库文章，无法重复转换");
        }

        // 验证工单状态
        if (ticket.Status != TicketStatus.Resolved)
        {
            throw new InvalidOperationException($"工单状态为 {ticket.Status}，仅已解决状态的工单可转为知识库");
        }

        if (ticket.KbArticleId.HasValue)
        {
            throw new InvalidOperationException("该工单已转换为知识库文章，无法重复转换");
        }

        if (ticket.KbArticleId.HasValue)
        {
            throw new InvalidOperationException("该工单已转换为知识库文章，无法重复转换");
        }

        if (string.IsNullOrWhiteSpace(ticket.FinalSolutionSummary))
        {
            throw new InvalidOperationException("工单 final_solution_summary 为空，无法转为知识库");
        }

        // 从 meta_json 解析 AI 元数据（如果存在）
        string? issueCategory = null;
        string? alarmCode = null;
        if (ticket.Meta != null)
        {
            issueCategory = ticket.Meta.IssueCategory;
            alarmCode = ticket.Meta.AlarmCode;
        }

        // 构建知识库文章内容
        var title = string.IsNullOrWhiteSpace(issueCategory) && string.IsNullOrWhiteSpace(alarmCode)
            ? $"[{ticket.TicketNo}] {ticket.Title}"
            : $"[{ticket.TicketNo}] {issueCategory ?? ""} - {alarmCode ?? ""} - {ticket.Title}".TrimEnd(' ', '-');

        var questionText = ticket.Description ?? "无详细描述";

        // 原因分析：尝试从 meta_json 提取或由工单标题推断
        string causeText;
        if (!string.IsNullOrWhiteSpace(issueCategory))
        {
            causeText = $"根据 AI 智能客服判断，问题分类为：{issueCategory}";
            if (!string.IsNullOrWhiteSpace(alarmCode))
            {
                causeText += $"\n报警代码：{alarmCode}";
            }
        }
        else
        {
            causeText = "详见最终解决方案";
        }

        // 解决步骤使用最终的解决方案摘要
        var solutionText = ticket.FinalSolutionSummary;

        // 适用范围：使用设备信息填充
        string? scopeJson = null;
        if (!string.IsNullOrWhiteSpace(ticket.DeviceMn) || !string.IsNullOrWhiteSpace(ticket.DeviceId))
        {
            var scopeDict = new Dictionary<string, string>();
            if (!string.IsNullOrWhiteSpace(ticket.DeviceMn))
                scopeDict["device_mn"] = ticket.DeviceMn;
            if (!string.IsNullOrWhiteSpace(ticket.DeviceId))
                scopeDict["device_id"] = ticket.DeviceId;
            scopeJson = JsonSerializer.Serialize(scopeDict);
        }

        // 创建知识库文章
        var article = new KnowledgeArticle
        {
            TenantId = tenantId,
            Title = title,
            QuestionText = questionText,
            CauseText = causeText,
            SolutionText = solutionText,
            ScopeJson = scopeJson,
            Tags = $"工单，{ticket.TicketNo},{issueCategory ?? "未分类"}",
            Status = "draft",
            Version = 1,
            CreatedBy = userId,
            SourceType = "ticket",
            SourceId = ticket.TicketId.ToString(),
            CreatedAt = DateTime.Now
        };

        _context.KnowledgeArticles.Add(article);
        await _context.SaveChangesAsync();

        // 设置已转换的知识库文章 ID
        ticket.KbArticleId = article.Id;
        await _context.SaveChangesAsync();

        // 记录转为知识库日志
        await CreateLogAsync(
            ticketId,
            TicketLogAction.ConvertToKb,
            $"已转换为知识库文章（ID: {article.Id}，标题：{title})",
            userId,
            null,
            null);

        _logger.LogInformation("工单已转换为知识库文章：Ticket={TicketNo}, ArticleId={ArticleId}",
            ticket.TicketNo, article.Id);

        // 异步触发向量入库（失败不回滚）
        bool vectorSuccess = true;
        string vectorMessage = string.Empty;

        if (triggerVectorIndex)
        {
            try
            {
                var aiHubAiUrl = _configuration["AiHubAi:BaseUrl"];
                if (!string.IsNullOrWhiteSpace(aiHubAiUrl))
                {
                    var client = _httpClientFactory.CreateClient();
                    var ingestUrl = $"{aiHubAiUrl}/api/v1/ingest/article/{article.Id}";

                    _logger.LogInformation("正在触发向量入库：{Url}", ingestUrl);

                    using var response = await client.PostAsync(ingestUrl, null);

                    if (response.IsSuccessStatusCode)
                    {
                        vectorSuccess = true;
                        _logger.LogInformation("向量入库成功：ArticleId={ArticleId}", article.Id);
                    }
                    else
                    {
                        vectorSuccess = false;
                        vectorMessage = $"向量入库失败：HTTP {(int)response.StatusCode}";
                        _logger.LogWarning("向量入库失败：{Message}", vectorMessage);

                        // 记录失败的日志到 ticket_log
                        await CreateLogAsync(
                            ticketId,
                            TicketLogAction.ConvertToKb,
                            $"向量入库失败：{vectorMessage}",
                            userId,
                            null,
                            null);
                    }
                }
                else
                {
                    vectorSuccess = false;
                    vectorMessage = "未配置 AiHubAi:BaseUrl，跳过向量入库";
                    _logger.LogWarning(vectorMessage);
                }
            }
            catch (Exception ex)
            {
                vectorSuccess = false;
                vectorMessage = $"向量入库异常：{ex.Message}";
                _logger.LogError(ex, "触发向量入库时发生错误");

                // 记录失败日志
                await CreateLogAsync(
                    ticketId,
                    TicketLogAction.ConvertToKb,
                    vectorMessage,
                    userId,
                    null,
                    null);
            }
        }

        return (article.Id, $"已成功转换为知识库文章（文章 ID: {article.Id}）", vectorSuccess);
    }
}
