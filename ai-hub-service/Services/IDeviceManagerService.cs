namespace AiHub.Services
{
    /// <summary>
    /// 设备管理服务接口，用于验证机器号是否存在于 YH_8082.DeviceManager
    /// </summary>
    public interface IDeviceManagerService
    {
        /// <summary>
        /// 检查机器号（deviceMN）是否存在于 DeviceManager 表中
        /// </summary>
        /// <param name="deviceMN">机器号</param>
        /// <returns>存在返回 true，否则返回 false</returns>
        Task<bool> ExistsDeviceMNAsync(string deviceMN);
    }
}
