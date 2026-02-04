# AI Hub AI 服务 — 运维交付说明

## 部署完之后还需要改哪里？

| 必配项 | 说明 |
|--------|------|
| **1. 环境变量 / .env** | 镜像里**不含** `.env`（安全起见）。运行容器时必须挂载生产配置或传环境变量，否则连不上数据库、.NET、附件等。见下方「3）运行容器」挂载示例。 |
| **2. Nginx（若用）** | 把前端的「Python 接口」路径（如 `/python-api`）反向代理到本机 `http://127.0.0.1:<PORT>`（PORT 默认 8000，或你 `-p` 映射的端口）。 |
| **3. 前端接口地址** | 前端（如智能客服）请求 Python 的 base URL 要和实际访问一致：若通过 Nginx 用 `/python-api`，前端通常写相对路径即可；若直连，需配置为 `https://域名:端口`。 |
| **4. .NET 地址** | Python 内配置的 `DOTNET_BASE_URL` 要能在容器内访问到 .NET（同机用 `http://127.0.0.1:5000` 或 `http://host.docker.internal:5000`，跨机用实际 IP:端口）。 |

以上都配好后再用健康检查 `GET /health` 和实际对话接口验证。

### 如果改了端口（PORT 或默认 8000），需要改哪里？

| 位置 | 要改什么 |
|------|----------|
| **1. 本机/容器** | 用环境变量时：`python main.py` 和 Docker `CMD ["python", "main.py"]` 都会读 `PORT`，只需运行时设 `-e PORT=9000`；若改的是代码里默认值 `"8000"`，只改根目录 `main.py` 里那一处即可。 |
| **2. Dockerfile** | 若固定用非 8000 端口：改 `ENV PORT=xxx` 和 `EXPOSE xxx`。若用 `PORT` 环境变量，则 `EXPOSE` 可保留 8000（仅文档意义），或改成你常用端口。 |
| **3. 运行容器** | `-p 宿主机端口:容器端口` 里「容器端口」要等于实际监听端口（即 `PORT`）。例如 `PORT=9000` 则 `-p 9000:9000` 或 `-p 80:9000`。 |
| **4. README-OPS / 健康检查** | 文档里的示例端口、`curl http://localhost:8000/health` 改成你实际端口。 |
| **5. Nginx** | `proxy_pass http://127.0.0.1:8000` 改成 `http://127.0.0.1:<你的端口>`（或 upstream 里写的端口）。 |
| **6. 前端 after-sales-ai** | 仅**本地开发**且连本机 Python 时要改：`vite.config.ts` 里 `proxy.target`（如 `http://localhost:8000` → 你的端口）。**生产环境**前端用相对路径 `/python-api`，由 Nginx 转发到后端端口，改 Nginx 即可，**不用改 after-sales-ai 代码**。 |

**推荐**：尽量用环境变量 `PORT`，运行时 `-e PORT=9000`；这样只需改「运行命令、Nginx」；只有本地开发前端时要改 after-sales-ai 的 vite 代理。

---

## 1）服务结论（定位结果）

| 项 | 值 |
|----|-----|
| **服务类型** | FastAPI |
| **入口** | `app.main:app` |
| **端口** | 默认 **8000**，可由环境变量 **PORT** 覆盖 |
| **依赖文件** | 根目录 `requirements.txt` 已存在 |

启动方式：`python main.py`（根目录 `main.py` 里读 `PORT`，默认 8000）。Docker 中也可在运行时传 `-e PORT=9000` 改端口。

健康检查：`GET http://<host>:<PORT>/health` 返回 `{"ok": true, "status": "ok", "service": "ai-hub-ai"}`，可用于存活探针。

**生产环境实际地址**：API 文档与服务当前运行在 **http://www.yonghongjituan.com:6714**（端口 6714），接口文档：http://www.yonghongjituan.com:6714/docs 。

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
