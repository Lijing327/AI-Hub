# AI Hub Excel 导入服务

FastAPI 服务，用于处理 Excel 文件导入并转换为知识条目。

## 功能

- 接收 Excel (.xlsx) 文件
- 使用 pandas/openpyxl 解析 Excel
- 将每行映射为知识条目（按约定规则）
- 调用 .NET 后端内部 API 批量创建草稿
- 返回导入统计和失败详情

## 安装

```bash
# 安装依赖
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
DOTNET_BASE_URL=http://localhost:5000
INTERNAL_TOKEN=your-internal-token-change-in-production
DEFAULT_TENANT=default
```

**重要**：`INTERNAL_TOKEN` 必须与 .NET 后端 `appsettings.json` 中的 `InternalToken` 一致。

## 运行

### 方式 1：使用启动脚本（推荐）

**Windows (PowerShell)**：
```powershell
.\start.ps1
```

**Linux/Mac (Bash)**：
```bash
chmod +x start.sh
./start.sh
```

### 方式 2：直接使用 uvicorn 命令

```bash
# 开发模式（推荐）
.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 或 Linux/Mac
.venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 方式 3：直接运行 main.py（不推荐）

```bash
.venv\Scripts\python.exe main.py
```

**注意**：如果端口 8000 被占用，可以：
- 修改 `start.ps1` 或 `start.sh` 中的端口号
- 或设置环境变量：`$env:PORT=8001`（PowerShell）或 `export PORT=8001`（Bash）

服务启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## API 接口

### POST /import/excel

导入 Excel 文件为知识条目。

**请求**：
- Content-Type: `multipart/form-data`
- Body: `file` (Excel 文件)

**响应**：
```json
{
  "total_rows": 10,
  "success_count": 8,
  "failure_count": 2,
  "article_ids": [1, 2, 3, 4, 5, 6, 7, 8],
  "failures": [
    {
      "row_index": 5,
      "reason": "Title 不能为空"
    },
    {
      "row_index": 9,
      "reason": "数据库错误"
    }
  ]
}
```

## Excel 格式要求

### 必需字段
- **设备型号**：设备或系统的型号
- **故障现象**：故障的具体表现

### 可选字段
- **报警信息**：报警码、提示信息等
- **原因分析**：可能的原因（支持多行，自动格式化为"原因 1/2/3"）
- **处理方法**：解决步骤（支持多行，自动格式化为"步骤 1/2/3"）

### 示例

| 设备型号 | 故障现象 | 报警信息 | 原因分析 | 处理方法 |
|---------|---------|---------|---------|---------|
| YH-100 | 启动后无法进入自动模式 | 无报警码 | 安全门未完全关闭<br>液压站压力不足 | 检查安全门状态<br>检查液压站压力表<br>重新尝试切换 |

## 字段映射规则

1. **title**：`设备型号 + 故障现象`
2. **question_text**：结构化格式（【发生场景】、【具体表现】、【报警信息】、【影响范围】）
3. **cause_text**：自动格式化为"原因 1/2/3"格式
4. **solution_text**：自动格式化为"步骤 1/2/3"格式
5. **scope_json**：`{"设备型号": "xxx"}`
6. **tags**：设备型号、报警信息、来源文档名
7. **status**：`draft`（草稿）
8. **created_by**：`系统导入`

## 使用示例

### curl

```bash
curl -X POST "http://localhost:8000/import/excel" \
  -F "file=@YH系列造型机常见故障及处置明细.xlsx"
```

### Python

```python
import httpx

with open("YH系列造型机常见故障及处置明细.xlsx", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/import/excel",
        files={"file": f}
    )
    print(response.json())
```

## 注意事项

1. 确保 .NET 后端服务已启动
2. 确保 `INTERNAL_TOKEN` 配置正确
3. Excel 文件第一行必须是表头
4. 数据从第二行开始
5. 空行会自动跳过
6. 单行处理失败不影响其他行
