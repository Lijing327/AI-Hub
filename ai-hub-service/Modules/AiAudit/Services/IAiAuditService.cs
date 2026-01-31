using ai_hub_service.Modules.AiAudit.Dtos;

namespace ai_hub_service.Modules.AiAudit.Services;

/// <summary>
/// AI 审计服务接口
/// </summary>
public interface IAiAuditService
{
    // ========== 写入操作（供 Python 调用）==========
    
    /// <summary>创建会话</summary>
    Task<StartConversationResponse> StartConversationAsync(StartConversationRequest request);

    /// <summary>追加消息</summary>
    Task<AppendMessageResponse> AppendMessageAsync(AppendMessageRequest request);

    /// <summary>记录决策</summary>
    Task<AuditOperationResponse> LogDecisionAsync(LogDecisionRequest request);

    /// <summary>记录 RAG 检索</summary>
    Task<AuditOperationResponse> LogRetrievalAsync(LogRetrievalRequest request);

    /// <summary>记录响应</summary>
    Task<AuditOperationResponse> LogResponseAsync(LogResponseRequest request);

    /// <summary>结束会话</summary>
    Task<AuditOperationResponse> EndConversationAsync(EndConversationRequest request);

    // ========== 查询操作（供管理后台）==========

    /// <summary>查询会话列表</summary>
    Task<(List<ConversationListItem> Items, int TotalCount)> GetConversationListAsync(ConversationListQuery query);

    /// <summary>获取会话详情（含所有消息和日志）</summary>
    Task<ConversationDetail?> GetConversationDetailAsync(Guid conversationId);

    // ========== 统计操作 ==========

    /// <summary>获取统计概览</summary>
    Task<StatsOverview> GetStatsOverviewAsync(StatsQuery query);

    /// <summary>获取 Top 意图统计</summary>
    Task<List<IntentStat>> GetTopIntentsAsync(StatsQuery query, int top = 10);

    /// <summary>获取 Top 命中文档统计</summary>
    Task<List<DocHitStat>> GetTopDocsAsync(StatsQuery query, int top = 10);

    /// <summary>获取无命中问题列表</summary>
    Task<List<NoMatchQuestion>> GetNoMatchQuestionsAsync(StatsQuery query, int top = 50);
}
