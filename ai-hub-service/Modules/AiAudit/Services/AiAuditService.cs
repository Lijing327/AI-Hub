using ai_hub_service.Data;
using ai_hub_service.Modules.AiAudit.Dtos;
using ai_hub_service.Modules.AiAudit.Entities;
using Microsoft.EntityFrameworkCore;

namespace ai_hub_service.Modules.AiAudit.Services;

/// <summary>
/// AI 审计服务实现
/// </summary>
public class AiAuditService : IAiAuditService
{
    private readonly ApplicationDbContext _db;
    private readonly ILogger<AiAuditService> _logger;

    public AiAuditService(ApplicationDbContext db, ILogger<AiAuditService> logger)
    {
        _db = db;
        _logger = logger;
    }

    /// <summary>
    /// 将数据库读出的时间视为 UTC，确保 API 返回带 Z 的 ISO 时间，前端可按本地时区正确显示
    /// </summary>
    private static DateTime AsUtc(DateTime value)
    {
        if (value.Kind == DateTimeKind.Utc) return value;
        return DateTime.SpecifyKind(value, DateTimeKind.Utc);
    }

    /// <summary>
    /// 将日期调整为当天结束时间（23:59:59.999）
    /// 用于日期范围查询时包含整天的数据
    /// </summary>
    private static DateTime? AdjustToEndOfDay(DateTime? date)
    {
        if (!date.HasValue) return null;
        // 如果时间部分是 00:00:00，说明只传了日期，需要调整为当天结束
        if (date.Value.TimeOfDay == TimeSpan.Zero)
        {
            return date.Value.Date.AddDays(1).AddMilliseconds(-1);
        }
        return date.Value;
    }

    // ========== 写入操作 ==========

    public async Task<StartConversationResponse> StartConversationAsync(StartConversationRequest request)
    {
        var conversation = new AiConversation
        {
            ConversationId = Guid.NewGuid(),
            TenantId = request.TenantId,
            UserId = request.UserId,
            Channel = request.Channel,
            MetaJson = request.MetaJson,
            StartedAt = DateTime.UtcNow,
            CreatedAt = DateTime.UtcNow
        };

        _db.AiConversations.Add(conversation);
        await _db.SaveChangesAsync();

        _logger.LogInformation("创建会话: {ConversationId}, tenant={TenantId}, channel={Channel}",
            conversation.ConversationId, conversation.TenantId, conversation.Channel);

        return new StartConversationResponse
        {
            ConversationId = conversation.ConversationId,
            StartedAt = conversation.StartedAt
        };
    }

    public async Task<AppendMessageResponse> AppendMessageAsync(AppendMessageRequest request)
    {
        var message = new AiMessage
        {
            MessageId = Guid.NewGuid(),
            ConversationId = request.ConversationId,
            Role = request.Role,
            Content = request.Content,
            ContentLen = request.Content?.Length ?? 0,
            IsMasked = request.IsMasked,
            MaskedContent = request.MaskedContent,
            CreatedAt = DateTime.UtcNow
        };

        _db.AiMessages.Add(message);
        await _db.SaveChangesAsync();

        _logger.LogDebug("追加消息: {MessageId}, conv={ConversationId}, role={Role}",
            message.MessageId, message.ConversationId, message.Role);

        return new AppendMessageResponse
        {
            MessageId = message.MessageId,
            CreatedAt = message.CreatedAt
        };
    }

    public async Task<AuditOperationResponse> LogDecisionAsync(LogDecisionRequest request)
    {
        var decision = new AiDecisionLog
        {
            MessageId = request.MessageId,
            IntentType = request.IntentType,
            Confidence = request.Confidence,
            ModelName = request.ModelName,
            PromptVersion = request.PromptVersion,
            UseKnowledge = request.UseKnowledge,
            FallbackReason = request.FallbackReason,
            TokensIn = request.TokensIn,
            TokensOut = request.TokensOut,
            CreatedAt = DateTime.UtcNow
        };

        _db.AiDecisionLogs.Add(decision);
        await _db.SaveChangesAsync();

        _logger.LogDebug("记录决策: msg={MessageId}, intent={IntentType}, conf={Confidence}",
            request.MessageId, request.IntentType, request.Confidence);

        return new AuditOperationResponse { Success = true };
    }

    public async Task<AuditOperationResponse> LogRetrievalAsync(LogRetrievalRequest request)
    {
        if (request.Docs == null || request.Docs.Count == 0)
            return new AuditOperationResponse { Success = true, Message = "无检索结果" };

        var logs = request.Docs.Select(d => new AiRetrievalLog
        {
            MessageId = request.MessageId,
            DocId = d.DocId,
            DocTitle = d.DocTitle,
            Score = d.Score,
            Rank = d.Rank,
            ChunkId = d.ChunkId,
            CreatedAt = DateTime.UtcNow
        }).ToList();

        _db.AiRetrievalLogs.AddRange(logs);
        await _db.SaveChangesAsync();

        _logger.LogDebug("记录检索: msg={MessageId}, docs={Count}", request.MessageId, logs.Count);

        return new AuditOperationResponse { Success = true };
    }

    public async Task<AuditOperationResponse> LogResponseAsync(LogResponseRequest request)
    {
        var response = new AiResponse
        {
            MessageId = request.MessageId,
            FinalAnswer = request.FinalAnswer,
            ResponseTimeMs = request.ResponseTimeMs,
            IsSuccess = request.IsSuccess,
            ErrorType = request.ErrorType,
            ErrorDetail = request.ErrorDetail,
            CreatedAt = DateTime.UtcNow
        };

        _db.AiResponses.Add(response);
        await _db.SaveChangesAsync();

        _logger.LogDebug("记录响应: msg={MessageId}, time={TimeMs}ms, success={IsSuccess}",
            request.MessageId, request.ResponseTimeMs, request.IsSuccess);

        return new AuditOperationResponse { Success = true };
    }

    public async Task<AuditOperationResponse> EndConversationAsync(EndConversationRequest request)
    {
        var conversation = await _db.AiConversations.FindAsync(request.ConversationId);
        if (conversation == null)
            return new AuditOperationResponse { Success = false, Message = "会话不存在" };

        conversation.EndedAt = DateTime.UtcNow;
        await _db.SaveChangesAsync();

        _logger.LogInformation("结束会话: {ConversationId}", request.ConversationId);

        return new AuditOperationResponse { Success = true };
    }

    // ========== 查询操作 ==========

    public async Task<(List<ConversationListItem> Items, int TotalCount)> GetConversationListAsync(ConversationListQuery query)
    {
        var startTo = AdjustToEndOfDay(query.StartTo);

        var q = _db.AiConversations.AsNoTracking().AsQueryable();

        // 筛选条件
        if (!string.IsNullOrEmpty(query.TenantId))
            q = q.Where(c => c.TenantId == query.TenantId);
        if (!string.IsNullOrEmpty(query.UserId))
            q = q.Where(c => c.UserId == query.UserId);
        if (!string.IsNullOrEmpty(query.Channel))
            q = q.Where(c => c.Channel == query.Channel);
        if (query.StartFrom.HasValue)
            q = q.Where(c => c.StartedAt >= query.StartFrom.Value);
        if (startTo.HasValue)
            q = q.Where(c => c.StartedAt <= startTo.Value);

        // 意图/兜底筛选需要 join
        if (!string.IsNullOrEmpty(query.IntentType) || query.HasFallback.HasValue)
        {
            var convIds = _db.AiMessages
                .Join(_db.AiDecisionLogs, m => m.MessageId, d => d.MessageId, (m, d) => new { m.ConversationId, d.IntentType, d.FallbackReason })
                .AsQueryable();

            if (!string.IsNullOrEmpty(query.IntentType))
                convIds = convIds.Where(x => x.IntentType == query.IntentType);
            if (query.HasFallback == true)
                convIds = convIds.Where(x => x.FallbackReason != null);
            if (query.HasFallback == false)
                convIds = convIds.Where(x => x.FallbackReason == null);

            var filteredIds = convIds.Select(x => x.ConversationId).Distinct();
            q = q.Where(c => filteredIds.Contains(c.ConversationId));
        }

        var totalCount = await q.CountAsync();

        var items = await q
            .OrderByDescending(c => c.StartedAt)
            .Skip((query.Page - 1) * query.PageSize)
            .Take(query.PageSize)
            .Select(c => new ConversationListItem
            {
                ConversationId = c.ConversationId,
                TenantId = c.TenantId,
                UserId = c.UserId,
                Channel = c.Channel,
                StartedAt = AsUtc(c.StartedAt),
                EndedAt = c.EndedAt.HasValue ? AsUtc(c.EndedAt.Value) : null,
                MessageCount = c.Messages.Count,
                // 主意图取第一条决策
                MainIntent = _db.AiDecisionLogs
                    .Where(d => _db.AiMessages.Where(m => m.ConversationId == c.ConversationId).Select(m => m.MessageId).Contains(d.MessageId))
                    .OrderBy(d => d.CreatedAt)
                    .Select(d => d.IntentType)
                    .FirstOrDefault(),
                // 是否有兜底
                HasFallback = _db.AiDecisionLogs
                    .Where(d => _db.AiMessages.Where(m => m.ConversationId == c.ConversationId).Select(m => m.MessageId).Contains(d.MessageId))
                    .Any(d => d.FallbackReason != null),
                // 平均响应时间
                AvgResponseTimeMs = (int?)_db.AiResponses
                    .Where(r => _db.AiMessages.Where(m => m.ConversationId == c.ConversationId).Select(m => m.MessageId).Contains(r.MessageId))
                    .Average(r => (int?)r.ResponseTimeMs)
            })
            .ToListAsync();

        return (items, totalCount);
    }

    public async Task<ConversationDetail?> GetConversationDetailAsync(Guid conversationId)
    {
        var conversation = await _db.AiConversations
            .AsNoTracking()
            .FirstOrDefaultAsync(c => c.ConversationId == conversationId);

        if (conversation == null)
            return null;

        var messages = await _db.AiMessages
            .AsNoTracking()
            .Where(m => m.ConversationId == conversationId)
            .OrderBy(m => m.CreatedAt)
            .ToListAsync();

        var messageIds = messages.Select(m => m.MessageId).ToList();

        var decisions = await _db.AiDecisionLogs
            .AsNoTracking()
            .Where(d => messageIds.Contains(d.MessageId))
            .ToDictionaryAsync(d => d.MessageId);

        var retrievals = await _db.AiRetrievalLogs
            .AsNoTracking()
            .Where(r => messageIds.Contains(r.MessageId))
            .GroupBy(r => r.MessageId)
            .ToDictionaryAsync(g => g.Key, g => g.OrderBy(r => r.Rank).ToList());

        var responses = await _db.AiResponses
            .AsNoTracking()
            .Where(r => messageIds.Contains(r.MessageId))
            .ToDictionaryAsync(r => r.MessageId);

        return new ConversationDetail
        {
            ConversationId = conversation.ConversationId,
            TenantId = conversation.TenantId,
            UserId = conversation.UserId,
            Channel = conversation.Channel,
            StartedAt = AsUtc(conversation.StartedAt),
            EndedAt = conversation.EndedAt.HasValue ? AsUtc(conversation.EndedAt.Value) : null,
            MetaJson = conversation.MetaJson,
            Messages = messages.Select(m => new MessageDetail
            {
                MessageId = m.MessageId,
                Role = m.Role,
                Content = m.IsMasked && !string.IsNullOrEmpty(m.MaskedContent) ? m.MaskedContent : m.Content,
                CreatedAt = AsUtc(m.CreatedAt),
                Decision = decisions.TryGetValue(m.MessageId, out var d) ? new DecisionDetail
                {
                    IntentType = d.IntentType,
                    Confidence = d.Confidence,
                    ModelName = d.ModelName,
                    PromptVersion = d.PromptVersion,
                    UseKnowledge = d.UseKnowledge,
                    FallbackReason = d.FallbackReason,
                    TokensIn = d.TokensIn,
                    TokensOut = d.TokensOut
                } : null,
                Retrievals = retrievals.TryGetValue(m.MessageId, out var rs) ? rs.Select(r => new RetrievalDetail
                {
                    DocId = r.DocId,
                    DocTitle = r.DocTitle,
                    Score = r.Score,
                    Rank = r.Rank
                }).ToList() : null,
                Response = responses.TryGetValue(m.MessageId, out var resp) ? new ResponseDetail
                {
                    FinalAnswer = resp.FinalAnswer,
                    ResponseTimeMs = resp.ResponseTimeMs,
                    IsSuccess = resp.IsSuccess,
                    ErrorType = resp.ErrorType,
                    ErrorDetail = resp.ErrorDetail
                } : null
            }).ToList()
        };
    }

    // ========== 统计操作 ==========

    public async Task<StatsOverview> GetStatsOverviewAsync(StatsQuery query)
    {
        try
        {
            // 调整结束日期为当天 23:59:59
            var startTo = AdjustToEndOfDay(query.StartTo);

            // 会话查询基础
            var convQuery = _db.AiConversations.AsNoTracking().AsQueryable();
            if (!string.IsNullOrEmpty(query.TenantId))
                convQuery = convQuery.Where(c => c.TenantId == query.TenantId);
            if (query.StartFrom.HasValue)
                convQuery = convQuery.Where(c => c.StartedAt >= query.StartFrom.Value);
            if (startTo.HasValue)
                convQuery = convQuery.Where(c => c.StartedAt <= startTo.Value);

            var totalConversations = await convQuery.CountAsync();
            
            // 时间范围内的消息
            var msgQuery = _db.AiMessages.AsNoTracking().AsQueryable();
            if (query.StartFrom.HasValue)
                msgQuery = msgQuery.Where(m => m.CreatedAt >= query.StartFrom.Value);
            if (startTo.HasValue)
                msgQuery = msgQuery.Where(m => m.CreatedAt <= startTo.Value);
            
            var totalMessages = await msgQuery.CountAsync();

            // 决策统计
            var decisionQuery = _db.AiDecisionLogs.AsNoTracking().AsQueryable();
            if (query.StartFrom.HasValue)
                decisionQuery = decisionQuery.Where(d => d.CreatedAt >= query.StartFrom.Value);
            if (startTo.HasValue)
                decisionQuery = decisionQuery.Where(d => d.CreatedAt <= startTo.Value);

            var totalDecisions = await decisionQuery.CountAsync();
            var fallbackCount = await decisionQuery.Where(d => d.FallbackReason != null).CountAsync();
            var lowConfidenceCount = await decisionQuery.Where(d => d.Confidence < 0.5m).CountAsync();
            var knowledgeUsageCount = await decisionQuery.Where(d => d.UseKnowledge).CountAsync();

            // 响应统计
            var responseQuery = _db.AiResponses.AsNoTracking().AsQueryable();
            if (query.StartFrom.HasValue)
                responseQuery = responseQuery.Where(r => r.CreatedAt >= query.StartFrom.Value);
            if (startTo.HasValue)
                responseQuery = responseQuery.Where(r => r.CreatedAt <= startTo.Value);

            var totalResponses = await responseQuery.CountAsync();
            var successCount = await responseQuery.Where(r => r.IsSuccess).CountAsync();
            var avgResponseTime = totalResponses > 0 
                ? (int)await responseQuery.AverageAsync(r => r.ResponseTimeMs)
                : 0;

            return new StatsOverview
            {
                TotalConversations = totalConversations,
                TotalMessages = totalMessages,
            FallbackRate = totalDecisions > 0 ? Math.Round((decimal)fallbackCount / totalDecisions * 100, 2) : 0,
            LowConfidenceRate = totalDecisions > 0 ? Math.Round((decimal)lowConfidenceCount / totalDecisions * 100, 2) : 0,
            AvgResponseTimeMs = avgResponseTime,
            SuccessRate = totalResponses > 0 ? Math.Round((decimal)successCount / totalResponses * 100, 2) : 0,
            KnowledgeUsageRate = totalDecisions > 0 ? Math.Round((decimal)knowledgeUsageCount / totalDecisions * 100, 2) : 0
            };
        }
        catch (Exception ex)
        {
            _logger.LogWarning("获取统计概览失败（表可能不存在）: {Error}", ex.Message);
            return new StatsOverview();
        }
    }

    public async Task<List<IntentStat>> GetTopIntentsAsync(StatsQuery query, int top = 10)
    {
        try
        {
            var startTo = AdjustToEndOfDay(query.StartTo);

            var decisionQuery = _db.AiDecisionLogs.AsNoTracking().AsQueryable();
            if (query.StartFrom.HasValue)
                decisionQuery = decisionQuery.Where(d => d.CreatedAt >= query.StartFrom.Value);
            if (startTo.HasValue)
                decisionQuery = decisionQuery.Where(d => d.CreatedAt <= startTo.Value);

            var total = await decisionQuery.CountAsync();
            if (total == 0)
                return new List<IntentStat>();

            var intents = await decisionQuery
                .GroupBy(d => d.IntentType)
                .Select(g => new { IntentType = g.Key, Count = g.Count() })
                .OrderByDescending(x => x.Count)
                .Take(top)
                .ToListAsync();

            return intents
                .Where(i => !string.IsNullOrEmpty(i.IntentType))
                .Select(i => new IntentStat
                {
                    IntentType = i.IntentType,
                    Count = i.Count,
                    Percentage = total > 0 ? Math.Round((decimal)i.Count / total * 100, 2) : 0
                }).ToList();
        }
        catch (Exception ex)
        {
            _logger.LogWarning("获取意图统计失败（表可能不存在）: {Error}", ex.Message);
            return new List<IntentStat>();
        }
    }

    public async Task<List<DocHitStat>> GetTopDocsAsync(StatsQuery query, int top = 10)
    {
        try
        {
            var startTo = AdjustToEndOfDay(query.StartTo);

            var retrievalQuery = _db.AiRetrievalLogs.AsNoTracking().AsQueryable();
            if (query.StartFrom.HasValue)
                retrievalQuery = retrievalQuery.Where(r => r.CreatedAt >= query.StartFrom.Value);
            if (startTo.HasValue)
                retrievalQuery = retrievalQuery.Where(r => r.CreatedAt <= startTo.Value);

            var count = await retrievalQuery.CountAsync();
            if (count == 0)
                return new List<DocHitStat>();

            var docs = await retrievalQuery
                .Where(r => !string.IsNullOrEmpty(r.DocId))
                .GroupBy(r => new { r.DocId, r.DocTitle })
                .Select(g => new 
                { 
                    g.Key.DocId, 
                    g.Key.DocTitle, 
                    HitCount = g.Count(),
                    AvgScore = g.Average(r => r.Score)
                })
                .OrderByDescending(x => x.HitCount)
                .Take(top)
                .ToListAsync();

            return docs.Select(d => new DocHitStat
            {
                DocId = d.DocId,
                DocTitle = d.DocTitle,
                HitCount = d.HitCount,
                AvgScore = Math.Round(d.AvgScore, 4)
            }).ToList();
        }
        catch (Exception ex)
        {
            _logger.LogWarning("获取文档命中统计失败（表可能不存在）: {Error}", ex.Message);
            return new List<DocHitStat>();
        }
    }

    public async Task<List<NoMatchQuestion>> GetNoMatchQuestionsAsync(StatsQuery query, int top = 50)
    {
        try
        {
            var startTo = AdjustToEndOfDay(query.StartTo);

            // 找出有 fallback_reason 的决策
            var decisionQuery = _db.AiDecisionLogs.AsNoTracking()
                .Where(d => d.FallbackReason != null);
            
            if (query.StartFrom.HasValue)
                decisionQuery = decisionQuery.Where(d => d.CreatedAt >= query.StartFrom.Value);
            if (startTo.HasValue)
                decisionQuery = decisionQuery.Where(d => d.CreatedAt <= startTo.Value);

            var count = await decisionQuery.CountAsync();
            if (count == 0)
                return new List<NoMatchQuestion>();

            // Join 获取原始问题
            var noMatchList = await decisionQuery
                .Join(_db.AiMessages,
                    d => d.MessageId,
                    m => m.MessageId,
                    (d, m) => new { d.MessageId, m.Content, d.CreatedAt, d.FallbackReason })
                .OrderByDescending(x => x.CreatedAt)
                .Take(top)
                .ToListAsync();

            return noMatchList.Select(n => new NoMatchQuestion
            {
                MessageId = n.MessageId,
                Question = n.Content,
                CreatedAt = AsUtc(n.CreatedAt),
                FallbackReason = n.FallbackReason
            }).ToList();
        }
        catch (Exception ex)
        {
            _logger.LogWarning("获取无命中问题失败（表可能不存在）: {Error}", ex.Message);
            return new List<NoMatchQuestion>();
        }
    }
}
