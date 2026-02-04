# AI Hub AI 服务 — 运维交付说明

## 1）服务结论（定位结果）

| 项 | 值 |
|----|-----|
| **服务类型** | FastAPI |
| **入口** | `app.main:app` |
| **端口** | 8000 |
| **依赖文件** | 根目录 `requirements.txt` 已存在 |

启动方式：`uvicorn app.main:app --host 0.0.0.0 --port 8000`（Dockerfile 已写死，无需改）。

健康检查：`GET http://<host>:8000/health` 返回 `{"ok": true, "status": "ok", "service": "ai-hub-ai"}`，可用于存活探针。

---

## 2）构建镜像

在项目根目录（与 Dockerfile 同目录）执行：

```bash
docker build -t ai-service:1.3.0 .
```

---

## 3）运行容器

```bash
docker run -d --name ai-service -p 8000:8000 ai-service:1.3.0
```

如需挂载配置或数据（例如生产环境 `.env`、Chroma 数据目录），可按需加 `-v`，例如：

```bash
docker run -d --name ai-service -p 8000:8000 \
  -v /path/on/host/.env.production:/app/.env \
  -v /path/on/host/data/chroma:/app/data/chroma \
  ai-service:1.3.0
```

---

## 4）查看日志

```bash
docker logs -f ai-service
```

---

## 5）导出给运维（离线交付）

```bash
docker save ai-service:1.3.0 -o ai-service_1.3.0.tar
```

将 `ai-service_1.3.0.tar` 拷贝给运维即可。

---

## 6）运维侧：导入并运行

```bash
docker load -i ai-service_1.3.0.tar
docker run -d --name ai-service -p 8000:8000 ai-service:1.3.0
```

---

## 7）验收（PowerShell）

在 **PowerShell** 中，于项目根目录执行：

```powershell
cd D:\00-Project\AI\AI-Hub\ai-hub-ai
docker build -t ai-service:1.3.0 .
docker images | findstr ai-service
```

**验收标准：**

1. `docker build -t ai-service:1.3.0 .` **不报错**。
2. `docker images` 能查到 **ai-service**，版本 **1.3.0**。
3. 启动后健康检查可通：
   ```powershell
   docker run -d --name ai-service -p 8000:8000 ai-service:1.3.0
   curl http://localhost:8000/health
   ```
   返回应包含 `"ok": true`。

（验收完成后可删除测试容器：`docker rm -f ai-service`。）
