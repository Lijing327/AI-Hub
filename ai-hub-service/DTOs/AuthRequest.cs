using System.ComponentModel.DataAnnotations;

namespace AiHub.DTOs
{
    public class LoginRequest
    {
        [Required]
        [StringLength(100, MinimumLength = 2)]
        public string Account { get; set; } = string.Empty;

        [Required]
        [StringLength(100, MinimumLength = 6)]
        public string Password { get; set; } = string.Empty;
    }

    public class RegisterRequest
    {
        [Required]
        [StringLength(100, MinimumLength = 2)]
        public string Account { get; set; } = string.Empty;

        [Required]
        [StringLength(100, MinimumLength = 6)]
        public string Password { get; set; } = string.Empty;

        /// <summary>
        /// 机器号（deviceMN），手机号注册时必填，需在 DeviceManager 表中存在
        /// </summary>
        public string? DeviceMN { get; set; }
    }

    public class ChangePasswordRequest
    {
        [Required]
        [StringLength(100, MinimumLength = 6)]
        public string CurrentPassword { get; set; } = string.Empty;

        [Required]
        [StringLength(100, MinimumLength = 6)]
        public string NewPassword { get; set; } = string.Empty;
    }

    public class UpdateProfileRequest
    {
        public string? Status { get; set; }
    }
}