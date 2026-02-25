using System.ComponentModel.DataAnnotations;

namespace AiHub.Models
{
    public class User
    {
        public string Id { get; set; } = string.Empty;

        [Required]
        [StringLength(20, MinimumLength = 11)]
        [Phone]
        public string Phone { get; set; } = string.Empty;

        [Required]
        public string PasswordHash { get; set; } = string.Empty;

        public string Status { get; set; } = "active";

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    }
}