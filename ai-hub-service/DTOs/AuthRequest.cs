using System.ComponentModel.DataAnnotations;

namespace AiHub.DTOs
{
    public class LoginRequest
    {
        [Required]
        [StringLength(20, MinimumLength = 11)]
        [Phone]
        public string Phone { get; set; } = string.Empty;

        [Required]
        [StringLength(100, MinimumLength = 6)]
        public string Password { get; set; } = string.Empty;
    }

    public class RegisterRequest
    {
        [Required]
        [StringLength(20, MinimumLength = 11)]
        [Phone]
        public string Phone { get; set; } = string.Empty;

        [Required]
        [StringLength(100, MinimumLength = 6)]
        public string Password { get; set; } = string.Empty;
    }
}