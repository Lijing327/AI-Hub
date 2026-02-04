# AI Hub 向量+对话服务（FastAPI）
FROM python:3.11-slim

WORKDIR /app

# 1️⃣ 安装系统级依赖（给 pyodbc 用）
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2️⃣ 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3️⃣ 拷贝源码
COPY . .

EXPOSE 8000

# 4️⃣ 启动服务
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
