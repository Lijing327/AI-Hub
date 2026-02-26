using AiHub.Models;
using AiHub.DTOs;
using AiHub.Utils;
using Microsoft.EntityFrameworkCore;
using ai_hub_service.Data;
using System.Text.RegularExpressions;

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
        private readonly IDeviceManagerService _deviceManagerService;

        public AuthService(ApplicationDbContext context, JwtUtils jwtUtils, PasswordHasher passwordHasher, IDeviceManagerService deviceManagerService)
        {
            _context = context;
            _jwtUtils = jwtUtils;
            _passwordHasher = passwordHasher;
            _deviceManagerService = deviceManagerService;
        }

        /// <summary>
        /// 标准化账号：手机号保持原样，邮箱转为小写，用户名保持原样
        /// </summary>
        private string NormalizeAccount(string account)
        {
            // 如果是邮箱，转为小写
            if (account.Contains('@'))
            {
                return account.ToLowerInvariant();
            }
            return account;
        }

        /// <summary>
        /// 验证账号格式（手机号/邮箱/用户名）
        /// </summary>
        private bool IsValidAccount(string account, out string error)
        {
            // 手机号验证（11 位数字，1 开头）
            if (Regex.IsMatch(account, @"^\d+$"))
            {
                if (!Regex.IsMatch(account, @"^1[3-9]\d{9}$"))
                {
                    error = "请输入正确的手机号";
                    return false;
                }
                error = "";
                return true;
            }

            // 邮箱验证
            if (account.Contains('@'))
            {
                if (!Regex.IsMatch(account, @"^[^\s@]+@[^\s@]+\.[^\s@]+$"))
                {
                    error = "请输入正确的邮箱";
                    return false;
                }
                error = "";
                return true;
            }

            // 用户名验证（至少 2 位）
            if (account.Length < 2)
            {
                error = "用户名长度至少 2 位";
                return false;
            }

            error = "";
            return true;
        }

        public async Task<AuthResponse> RegisterAsync(RegisterRequest request)
        {
            // 验证账号格式
            if (!IsValidAccount(request.Account, out var error))
            {
                throw new InvalidOperationException(error);
            }

            // 手机号注册时，必须提供机器号并在 DeviceManager 中验证
            if (Regex.IsMatch(request.Account, @"^\d+$"))
            {
                if (string.IsNullOrWhiteSpace(request.DeviceMN))
                {
                    throw new InvalidOperationException("手机号注册需填写机器号");
                }

                bool exists = await _deviceManagerService.ExistsDeviceMNAsync(request.DeviceMN.Trim());
                if (!exists)
                {
                    throw new InvalidOperationException("机器号不存在，请在设备管理表中确认");
                }
            }

            // 标准化账号
            var normalizedAccount = NormalizeAccount(request.Account);

            // 检查账号是否已存在
            var existingUser = await _context.Users
                .FirstOrDefaultAsync(u => u.Account == normalizedAccount);

            if (existingUser != null)
            {
                throw new InvalidOperationException("账号已注册");
            }

            // 检查机器号是否已被其他用户绑定（手机号注册时）
            if (!string.IsNullOrWhiteSpace(request.DeviceMN))
            {
                var boundUser = await _context.Users
                    .FirstOrDefaultAsync(u => u.DeviceMN == request.DeviceMN.Trim());
                if (boundUser != null)
                {
                    throw new InvalidOperationException("该机器号已被其他账号绑定");
                }
            }

            // 创建新用户
            var user = new User
            {
                Id = Guid.NewGuid().ToString(),
                Account = normalizedAccount,
                PasswordHash = _passwordHasher.HashPassword(request.Password),
                Status = "active",
                DeviceMN = !string.IsNullOrWhiteSpace(request.DeviceMN) ? request.DeviceMN.Trim() : null
            };

            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            // 生成 JWT token
            var token = _jwtUtils.GenerateToken(user.Id, user.Account);

            return new AuthResponse
            {
                Token = token,
                User = new UserInfo
                {
                    Id = user.Id,
                    Account = user.Account,
                    CreatedAt = user.CreatedAt
                }
            };
        }

        public async Task<AuthResponse> LoginAsync(LoginRequest request)
        {
            // 验证账号格式
            if (!IsValidAccount(request.Account, out var error))
            {
                throw new InvalidOperationException(error);
            }

            // 标准化账号
            var normalizedAccount = NormalizeAccount(request.Account);

            // 查询用户（支持手机号、邮箱、用户名登录）
            var user = await _context.Users
                .FirstOrDefaultAsync(u => u.Account == normalizedAccount && u.Status == "active");

            if (user == null || !_passwordHasher.VerifyPassword(request.Password, user.PasswordHash))
            {
                throw new UnauthorizedAccessException("账号或密码错误");
            }

            // 生成 JWT token
            var token = _jwtUtils.GenerateToken(user.Id, user.Account);

            return new AuthResponse
            {
                Token = token,
                User = new UserInfo
                {
                    Id = user.Id,
                    Account = user.Account,
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
