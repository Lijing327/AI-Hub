using System.ComponentModel.DataAnnotations;

namespace AiHub.Models
{
    public class User
    {
        public string Id { get; set; } = string.Empty;

        [Required]
        [StringLength(100, MinimumLength = 2)]
        public string Account { get; set; } = string.Empty;

        [Required]
        public string PasswordHash { get; set; } = string.Empty;

        public string Status { get; set; } = "active";

        /// <summary>
        /// 角色：user（普通用户）/ engineer（工程师）/ admin（管理员）
        /// 工程师和管理员可访问 /api/admin/tickets
        /// </summary>
        public string Role { get; set; } = "user";

        /// <summary>
        /// 机器号（deviceMN），与 DeviceManager 表绑定，手机号注册时必填
        /// </summary>
        public string? DeviceMN { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    }
}