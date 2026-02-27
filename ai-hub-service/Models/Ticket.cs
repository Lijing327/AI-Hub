using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace AiHub.Models;

/// <summary>
/// 工单状态枚举
/// </summary>
public static class TicketStatus
{
    public const string Pending = "pending";      // 待处理
    public const string Processing = "processing"; // 处理中
    public const string Resolved = "resolved";     // 已解决
    public const string Closed = "closed";         // 已关闭
}

/// <summary>
/// 工单优先级枚举
/// </summary>
public static class TicketPriority
{
    public const string Low = "low";
    public const string Medium = "medium";
    public const string High = "high";
    public const string Urgent = "urgent";
}

/// <summary>
/// 工单来源枚举
/// </summary>
public static class TicketSource
{
    public const string AiChat = "ai_chat";
    public const string Manual = "manual";
    public const string Api = "api";
}

/// <summary>
/// 工单主表实体 (ticket)
/// </summary>
[Table("ticket")]
public class Ticket
{
    /// <summary>
    /// 工单 ID
    /// </summary>
    [Key]
    [Column("ticket_id")]
    public Guid TicketId { get; set; } = Guid.NewGuid();

    /// <summary>
    /// 租户 ID
    /// </summary>
    [Required]
    [MaxLength(64)]
    [Column("tenant_id")]
    public string TenantId { get; set; } = string.Empty;

    /// <summary>
    /// 工单号（如 T202602260001）
    /// </summary>
    [Required]
    [MaxLength(32)]
    [Column("ticket_no")]
    public string TicketNo { get; set; } = string.Empty;

    /// <summary>
    /// 标题
    /// </summary>
    [Required]
    [MaxLength(256)]
    [Column("title")]
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// 问题描述
    /// </summary>
    [Column("description", TypeName = "NVARCHAR(MAX)")]
    public string? Description { get; set; }

    /// <summary>
    /// 状态：pending/processing/resolved/closed
    /// </summary>
    [Required]
    [MaxLength(20)]
    [Column("status")]
    public string Status { get; set; } = TicketStatus.Pending;

    /// <summary>
    /// 优先级：low/medium/high/urgent
    /// </summary>
    [Required]
    [MaxLength(10)]
    [Column("priority")]
    public string Priority { get; set; } = TicketPriority.Medium;

    /// <summary>
    /// 来源：ai_chat/manual/api
    /// </summary>
    [Required]
    [MaxLength(20)]
    [Column("source")]
    public string Source { get; set; } = TicketSource.Manual;

    /// <summary>
    /// 客户 ID
    /// </summary>
    [MaxLength(64)]
    [Column("customer_id")]
    public string? CustomerId { get; set; }

    /// <summary>
    /// 设备 ID
    /// </summary>
    [MaxLength(64)]
    [Column("device_id")]
    public string? DeviceId { get; set; }

    /// <summary>
    /// 设备 MN 号
    /// </summary>
    [MaxLength(64)]
    [Column("device_mn")]
    public string? DeviceMn { get; set; }

    /// <summary>
    /// 关联的会话 ID（ai_conversation.conversation_id）
    /// </summary>
    [Column("session_id")]
    public Guid? SessionId { get; set; }

    /// <summary>
    /// 触发工单的 AI 消息 ID（ai_message.message_id）
    /// </summary>
    [Column("trigger_message_id")]
    public Guid? TriggerMessageId { get; set; }

    /// <summary>
    /// 处理人 ID
    /// </summary>
    [MaxLength(64)]
    [Column("assignee_id")]
    public string? AssigneeId { get; set; }

    /// <summary>
    /// 处理人姓名（冗余）
    /// </summary>
    [MaxLength(64)]
    [Column("assignee_name")]
    public string? AssigneeName { get; set; }

    /// <summary>
    /// 创建人 ID
    /// </summary>
    [Required]
    [MaxLength(64)]
    [Column("created_by")]
    public string CreatedBy { get; set; } = string.Empty;

    /// <summary>
    /// 创建时间
    /// </summary>
    [Required]
    [Column("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.Now;

    /// <summary>
    /// 更新时间
    /// </summary>
    [Column("updated_at")]
    public DateTime? UpdatedAt { get; set; }

    /// <summary>
    /// 关闭时间
    /// </summary>
    [Column("closed_at")]
    public DateTime? ClosedAt { get; set; }

    /// <summary>
    /// 最终解决方案摘要（仅当 resolved 时填写）
    /// </summary>
    [Column("final_solution_summary", TypeName = "NVARCHAR(MAX)")]
    public string? FinalSolutionSummary { get; set; }

    /// <summary>
    /// 扩展信息（JSON 格式）- 存储 AI 返回的 issue_category、alarm_code、cited_docs 等
    /// 对应请求/响应中的 meta 字段，数据库存储为 JSON 字符串
    /// </summary>
    [Column("meta_json", TypeName = "NVARCHAR(MAX)")]
    public string? MetaJson { get; set; }

    public class TicketMeta
    {
        public string IssueCategory { get; set; }
        public string AlarmCode { get; set; }
        public List<string> CitedDocs { get; set; } = new List<string>();
    }

    [NotMapped]
    public TicketMeta Meta
    {
        get
        {
            if (string.IsNullOrEmpty(MetaJson))
                return null;
            return System.Text.Json.JsonSerializer.Deserialize<TicketMeta>(MetaJson);
        }
        set
        {
            MetaJson = value == null
                ? null
                : System.Text.Json.JsonSerializer.Serialize(value);
        }
    }

    /// <summary>
    /// 已转换的知识库文章 ID（防止重复转换）
    /// 需执行迁移 012_AddKbArticleIdToTicket.sql 后，数据库才有此列；未迁移前用 NotMapped 避免查询报错
    /// </summary>
    [Column("kb_article_id")]
    [NotMapped]
    public int? KbArticleId { get; set; }
}
