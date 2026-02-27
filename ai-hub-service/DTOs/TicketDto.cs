namespace AiHub.DTOs;

/// <summary>
/// Meta 对象（用于请求/响应）
/// </summary>
public class TicketMeta
{
    /// <summary>
    /// 问题分类
    /// </summary>
    public string? IssueCategory { get; set; }

    /// <summary>
    /// 报警代码
    /// </summary>
    public string? AlarmCode { get; set; }

    /// <summary>
    /// 引用的文档
    /// </summary>
    public List<string>? CitedDocs { get; set; }

    /// <summary>
    /// 其他扩展字段
    /// </summary>
    public System.Text.Json.Nodes.JsonNode? Extra { get; set; }
}

/// <summary>
/// 工单列表项 DTO
/// </summary>
public class TicketListDto
{
    public Guid TicketId { get; set; }
    public string TicketNo { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string Priority { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
    public string? DeviceMn { get; set; }
    public string? AssigneeName { get; set; }
    public string CreatedBy { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
}

/// <summary>
/// 工单详情 DTO
/// </summary>
public class TicketDetailDto
{
    public Guid TicketId { get; set; }
    public string TicketNo { get; set; } = string.Empty;
    public string TenantId { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string Status { get; set; } = string.Empty;
    public string Priority { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
    public string? CustomerId { get; set; }
    public string? DeviceId { get; set; }
    public string? DeviceMn { get; set; }
    public Guid? SessionId { get; set; }
    public Guid? TriggerMessageId { get; set; }
    public string? AssigneeId { get; set; }
    public string? AssigneeName { get; set; }
    public string CreatedBy { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
    public DateTime? ClosedAt { get; set; }
    public string? FinalSolutionSummary { get; set; }
    /// <summary>
    /// 扩展元数据（对象形式，数据库存储为 JSON 字符串）
    /// </summary>
    public TicketMeta? Meta { get; set; }
    /// <summary>
    /// 已转换的知识库文章 ID（存在则表示已转换过）
    /// </summary>
    public int? KbArticleId { get; set; }
    public List<TicketLogDto> Logs { get; set; } = new();
}

/// <summary>
/// 工单日志 DTO
/// </summary>
public class TicketLogDto
{
    public long LogId { get; set; }
    public Guid TicketId { get; set; }
    public string Action { get; set; } = string.Empty;
    public string? Content { get; set; }
    public string OperatorId { get; set; } = string.Empty;
    public string? OperatorName { get; set; }
    public string? NextStatus { get; set; }
    public DateTime CreatedAt { get; set; }
}

/// <summary>
/// 创建工单请求 DTO
/// </summary>
public class CreateTicketRequest
{
    /// <summary>
    /// 标题
    /// </summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// 问题描述
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// 优先级：low/medium/high/urgent
    /// </summary>
    public string? Priority { get; set; }

    /// <summary>
    /// 设备 ID
    /// </summary>
    public string? DeviceId { get; set; }

    /// <summary>
    /// 设备 MN 号
    /// </summary>
    public string? DeviceMn { get; set; }

    /// <summary>
    /// 客户 ID
    /// </summary>
    public string? CustomerId { get; set; }

    /// <summary>
    /// 会话 ID（关联 AI 对话）
    /// </summary>
    public Guid? SessionId { get; set; }

    /// <summary>
    /// 触发消息 ID（关联 AI 消息）
    /// </summary>
    public Guid? TriggerMessageId { get; set; }

    /// <summary>
    /// 来源：ai_chat/manual/api
    /// </summary>
    public string? Source { get; set; }

    /// <summary>
    /// 扩展元数据（对象形式）
    /// </summary>
    public TicketMeta? Meta { get; set; }
}

/// <summary>
/// 更新工单请求 DTO
/// </summary>
public class UpdateTicketRequest
{
    /// <summary>
    /// 标题
    /// </summary>
    public string? Title { get; set; }

    /// <summary>
    /// 问题描述
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// 优先级
    /// </summary>
    public string? Priority { get; set; }

    /// <summary>
    /// 处理人 ID
    /// </summary>
    public string? AssigneeId { get; set; }

    /// <summary>
    /// 处理人姓名
    /// </summary>
    public string? AssigneeName { get; set; }

    /// <summary>
    /// 最终解决方案摘要
    /// </summary>
    public string? FinalSolutionSummary { get; set; }

    /// <summary>
    /// 扩展元数据（对象形式）
    /// </summary>
    public TicketMeta? Meta { get; set; }
}

/// <summary>
/// 开始处理请求 DTO
/// </summary>
public class StartTicketRequest
{
    /// <summary>
    /// 处理人 ID（可选，不传则用当前用户）
    /// </summary>
    public string? AssigneeId { get; set; }

    /// <summary>
    /// 处理人姓名（可选）
    /// </summary>
    public string? AssigneeName { get; set; }

    /// <summary>
    /// 备注内容（可选）
    /// </summary>
    public string? Note { get; set; }
}

/// <summary>
/// 解决工单请求 DTO
/// </summary>
public class ResolveTicketRequest
{
    /// <summary>
    /// 最终解决方案摘要（必填）
    /// </summary>
    public string FinalSolutionSummary { get; set; } = string.Empty;

    /// <summary>
    /// 备注内容（可选）
    /// </summary>
    public string? Note { get; set; }
}

/// <summary>
/// 关闭工单请求 DTO
/// </summary>
public class CloseTicketRequest
{
    /// <summary>
    /// 备注内容（可选）
    /// </summary>
    public string? Note { get; set; }
}

/// <summary>
/// 添加工单日志请求 DTO
/// </summary>
public class CreateTicketLogRequest
{
    /// <summary>
    /// 日志内容
    /// </summary>
    public string Content { get; set; } = string.Empty;

    /// <summary>
    /// 操作人姓名（可选）
    /// </summary>
    public string? OperatorName { get; set; }
}

/// <summary>
/// 工单列表查询 DTO
/// </summary>
public class TicketQueryRequest
{
    /// <summary>
    /// 状态过滤
    /// </summary>
    public string? Status { get; set; }

    /// <summary>
    /// 优先级过滤
    /// </summary>
    public string? Priority { get; set; }

    /// <summary>
    /// 设备 MN 号过滤
    /// </summary>
    public string? DeviceMn { get; set; }

    /// <summary>
    /// 分配人 ID 过滤
    /// </summary>
    public string? AssigneeId { get; set; }

    /// <summary>
    /// 关键词搜索（标题/描述）
    /// </summary>
    public string? Keyword { get; set; }

    /// <summary>
    /// 页码（从 1 开始）
    /// </summary>
    public int PageIndex { get; set; } = 1;

    /// <summary>
    /// 每页数量
    /// </summary>
    public int PageSize { get; set; } = 20;
}

/// <summary>
/// 转换为知识库请求 DTO
/// </summary>
public class ConvertToKbRequest
{
    /// <summary>
    /// 是否触发向量入库（默认 true）
    /// </summary>
    public bool TriggerVectorIndex { get; set; } = true;
}
