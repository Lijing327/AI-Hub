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
        /// 机器号（deviceMN），与 DeviceManager 表绑定，手机号注册时必填
        /// </summary>
        public string? DeviceMN { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    }
}