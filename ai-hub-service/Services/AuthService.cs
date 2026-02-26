using AiHub.Models;
using AiHub.DTOs;
using AiHub.Utils;
using Microsoft.EntityFrameworkCore;
using ai_hub_service.Data;

namespace AiHub.Services
{
    public interface IAuthService
    {
        Task<AuthResponse> RegisterAsync(RegisterRequest request);
        Task<AuthResponse> LoginAsync(LoginRequest request);
        Task<User?> GetUserByIdAsync(string userId);
        Task<ChangePasswordResult> ChangePasswordAsync(string userId, string currentPassword, string newPassword);
        Task<UpdateProfileResult> UpdateProfileAsync(string userId, string? status);
    }

    public class AuthService : IAuthService
    {
        private readonly ApplicationDbContext _context;
        private readonly JwtUtils _jwtUtils;
        private readonly PasswordHasher _passwordHasher;

        public AuthService(ApplicationDbContext context, JwtUtils jwtUtils, PasswordHasher passwordHasher)
        {
            _context = context;
            _jwtUtils = jwtUtils;
            _passwordHasher = passwordHasher;
        }

        public async Task<AuthResponse> RegisterAsync(RegisterRequest request)
        {
            // 检查手机号是否已存在
            var existingUser = await _context.Users
                .FirstOrDefaultAsync(u => u.Phone == request.Phone);

            if (existingUser != null)
            {
                throw new InvalidOperationException("手机号已注册");
            }

            // 创建新用户
            var user = new User
            {
                Id = Guid.NewGuid().ToString(),
                Phone = request.Phone,
                PasswordHash = _passwordHasher.HashPassword(request.Password),
                Status = "active"
            };

            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            // 生成JWT token
            var token = _jwtUtils.GenerateToken(user.Id, user.Phone);

            return new AuthResponse
            {
                Token = token,
                User = new UserInfo
                {
                    Id = user.Id,
                    Phone = user.Phone,
                    CreatedAt = user.CreatedAt
                }
            };
        }

        public async Task<AuthResponse> LoginAsync(LoginRequest request)
        {
            var user = await _context.Users
                .FirstOrDefaultAsync(u => u.Phone == request.Phone && u.Status == "active");

            if (user == null || !_passwordHasher.VerifyPassword(request.Password, user.PasswordHash))
            {
                throw new UnauthorizedAccessException("手机号或密码错误");
            }

            // 生成JWT token
            var token = _jwtUtils.GenerateToken(user.Id, user.Phone);

            return new AuthResponse
            {
                Token = token,
                User = new UserInfo
                {
                    Id = user.Id,
                    Phone = user.Phone,
                    CreatedAt = user.CreatedAt
                }
            };
        }

        public async Task<User?> GetUserByIdAsync(string userId)
        {
            return await _context.Users.FindAsync(userId);
        }

        public async Task<ChangePasswordResult> ChangePasswordAsync(string userId, string currentPassword, string newPassword)
        {
            var user = await _context.Users.FindAsync(userId);
            if (user == null)
            {
                return new ChangePasswordResult
                {
                    Success = false,
                    Message = "用户不存在"
                };
            }

            if (!_passwordHasher.VerifyPassword(currentPassword, user.PasswordHash))
            {
                return new ChangePasswordResult
                {
                    Success = false,
                    Message = "当前密码错误"
                };
            }

            user.PasswordHash = _passwordHasher.HashPassword(newPassword);
            user.UpdatedAt = DateTime.UtcNow;
            await _context.SaveChangesAsync();

            return new ChangePasswordResult
            {
                Success = true,
                Message = "密码修改成功"
            };
        }

        public async Task<UpdateProfileResult> UpdateProfileAsync(string userId, string? status)
        {
            var user = await _context.Users.FindAsync(userId);
            if (user == null)
            {
                return new UpdateProfileResult
                {
                    Success = false,
                    Message = "用户不存在"
                };
            }

            if (!string.IsNullOrEmpty(status))
            {
                if (status != "active" && status != "disabled")
                {
                    return new UpdateProfileResult
                    {
                        Success = false,
                        Message = "无效的状态值，只能是 active 或 disabled"
                    };
                }
                user.Status = status;
            }

            user.UpdatedAt = DateTime.UtcNow;
            await _context.SaveChangesAsync();

            return new UpdateProfileResult
            {
                Success = true,
                Message = "资料更新成功"
            };
        }
    }
}