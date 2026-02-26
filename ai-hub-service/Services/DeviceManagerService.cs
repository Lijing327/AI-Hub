using Microsoft.Data.SqlClient;

namespace AiHub.Services
{
    /// <summary>
    /// 设备管理服务实现，从 172.16.15.9 的 YH_8082 数据库 DeviceManager 表查询 deviceMN
    /// 仅执行 SELECT 查询，不进行任何写操作
    /// </summary>
    public class DeviceManagerService : IDeviceManagerService
    {
        private readonly string _connectionString;
        private readonly ILogger<DeviceManagerService> _logger;

        public DeviceManagerService(IConfiguration configuration, ILogger<DeviceManagerService> logger)
        {
            string? connStr = configuration.GetConnectionString("DeviceManagerConnection");
            _connectionString = connStr ?? throw new InvalidOperationException("未配置 DeviceManagerConnection 连接字符串");
            _logger = logger;
        }

        /// <summary>
        /// 检查机器号是否存在于 [YH_8082].[dbo].[DeviceManager] 表
        /// </summary>
        public async Task<bool> ExistsDeviceMNAsync(string deviceMN)
        {
            if (string.IsNullOrWhiteSpace(deviceMN))
            {
                return false;
            }

            // 仅执行 SELECT 查询，符合安全规范（连接串指定 Database=YH_8082）
            string sql = "SELECT 1 FROM [dbo].[DeviceManager] WHERE [deviceMN] = @deviceMN";

            try
            {
                await using SqlConnection connection = new SqlConnection(_connectionString);
                await using SqlCommand command = new SqlCommand(sql, connection);
                command.Parameters.AddWithValue("@deviceMN", deviceMN.Trim());

                await connection.OpenAsync();
                object? result = await command.ExecuteScalarAsync();
                return result != null && result != DBNull.Value;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "查询 DeviceManager 表时发生错误，deviceMN={DeviceMN}", deviceMN);
                throw new InvalidOperationException("设备库查询失败，请稍后重试");
            }
        }
    }
}
