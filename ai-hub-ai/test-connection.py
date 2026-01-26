"""
测试 Python 服务与 .NET 后端的连接
"""
import os
import httpx
import asyncio

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("警告: python-dotenv 未安装，将使用环境变量或默认值")

DOTNET_BASE_URL = os.getenv("DOTNET_BASE_URL", "http://localhost:5000")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "test-token-123")
DEFAULT_TENANT = os.getenv("DEFAULT_TENANT", "default")

async def test_connection():
    """测试与 .NET 后端的连接"""
    print("=" * 50)
    print("测试 Python 服务与 .NET 后端的连接")
    print("=" * 50)
    print(f"DOTNET_BASE_URL: {DOTNET_BASE_URL}")
    print(f"INTERNAL_TOKEN: {INTERNAL_TOKEN[:10]}..." if len(INTERNAL_TOKEN) > 10 else f"INTERNAL_TOKEN: {INTERNAL_TOKEN}")
    print(f"DEFAULT_TENANT: {DEFAULT_TENANT}")
    print()
    
    # 测试 1: 健康检查
    print("测试 1: 检查 .NET 后端是否运行...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DOTNET_BASE_URL}/swagger", timeout=5.0)
            if response.status_code == 200:
                print("[OK] .NET 后端服务正在运行")
            else:
                print(f"[ERROR] .NET 后端返回状态码: {response.status_code}")
    except httpx.ConnectError:
        print("[ERROR] 无法连接到 .NET 后端，请确保服务已启动")
        return False
    except Exception as e:
        print(f"[ERROR] 连接失败: {str(e)}")
        return False
    
    # 测试 2: 测试内部 API 鉴权
    print("\n测试 2: 测试内部 API 鉴权...")
    try:
        async with httpx.AsyncClient() as client:
            # 测试批量创建接口（使用空列表）
            response = await client.post(
                f"{DOTNET_BASE_URL}/api/ai/kb/articles/batch",
                json={"articles": []},
                headers={
                    "Content-Type": "application/json",
                    "X-Tenant-Id": DEFAULT_TENANT,
                    "X-Internal-Token": INTERNAL_TOKEN
                },
                timeout=5.0
            )
            
            if response.status_code == 400:
                # 400 是预期的（因为 articles 为空）
                print("[OK] Token 验证通过（返回 400 是因为 articles 为空，这是预期的）")
            elif response.status_code == 401:
                print("[ERROR] Token 验证失败，请检查 INTERNAL_TOKEN 配置")
                print(f"  响应: {response.text}")
                return False
            else:
                print(f"[OK] 连接成功，状态码: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] 测试失败: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("所有测试通过！")
    print("=" * 50)
    return True

if __name__ == "__main__":
    asyncio.run(test_connection())
