using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using AiHub.Models;

namespace AiHub.Models;

/// <summary>
/// 工单日志操作类型
/// </summary>
public static class TicketLogAction
{
    public const string Create = "create";           // 创建工单
    public const string Start = "start";             // 开始处理
    public const string Resolve = "resolve";         // 标记已解决
    public const string Close = "close";             // 关闭工单
    public const string Comment = "comment";         // 添加备注
    public const string Reassign = "reassign";       // 转派
    public const string ConvertToKb = "convert_to_kb"; // 转为知识库
}

/// <summary>
/// 工单日志表实体 (ticket_log)
/// </summary>
[Table("ticket_log")]
public class TicketLog
{
    /// <summary>
    /// 日志 ID
    /// </summary>
    [Key]
    [Column("log_id")]
    public long LogId { get; set; }

    /// <summary>
    /// 工单 ID
    /// </summary>
    [Required]
    [Column("ticket_id")]
    public Guid TicketId { get; set; }

    /// <summary>
    /// 操作类型
    /// </summary>
    [Required]
    [MaxLength(64)]
    [Column("action")]
    public string Action { get; set; } = string.Empty;

    /// <summary>
    /// 日志内容
    /// </summary>
    [Column("content", TypeName = "NVARCHAR(MAX)")]
    public string? Content { get; set; }

    /// <summary>
    /// 操作人 ID
    /// </summary>
    [Required]
    [MaxLength(64)]
    [Column("operator_id")]
    public string OperatorId { get; set; } = string.Empty;

    /// <summary>
    /// 操作人姓名
    /// </summary>
    [MaxLength(64)]
    [Column("operator_name")]
    public string? OperatorName { get; set; }

    /// <summary>
    /// 变更后状态（可选）
    /// </summary>
    [MaxLength(20)]
    [Column("next_status")]
    public string? NextStatus { get; set; }

    /// <summary>
    /// 操作时间
    /// </summary>
    [Required]
    [Column("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.Now;
}
