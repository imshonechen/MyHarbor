# MyHarbor 环境变量说明

## 1. 使用说明

- 后端配置由 `backend/app/config.py` 的 `Settings` 管理，可通过环境变量覆盖默认值。
- 本地开发（在 `backend/` 目录运行 uvicorn）时，可在 `backend/.env` 放置配置；生产/Docker 部署建议在容器编排层注入环境变量。
- 未配置时使用默认值（见下表）。
- 注意：站点检测**间隔**不是环境变量，属于系统配置 `check_interval`（分钟），可在管理后台“系统设置”里修改（对应接口 `PUT /api/config`）。

## 2. 环境变量清单

### 2.1 后端环境变量

| 变量名 | 默认值 | 必填 | 说明 |
|------|------|------|------|
| `APP_NAME` | `MyHarbor API` | 否 | FastAPI 应用标题 |
| `APP_HOST` | `0.0.0.0` | 否 | 服务监听地址 |
| `APP_PORT` | `24041` | 否 | 后端服务端口 |
| `LOG_LEVEL` | `INFO` | 否 | 日志级别 |
| `DATABASE_URL` | `sqlite:///./data/myharbor.db` | 否 | 数据库连接串 |
| `JWT_SECRET` | `myharbor-dev-secret-change-me` | 是（生产） | JWT 签名密钥（生产必须更换强随机值） |
| `JWT_EXPIRE_HOURS` | `24` | 否 | Token 有效期（小时） |
| `CHECK_TIMEOUT_SECONDS` | `5` | 否 | 状态检测超时时间（秒） |
| `ENABLE_SCHEDULER` | `true` | 否 | 是否启用内置调度器（检测/聚合/清理） |

### 2.2 前端环境变量

| 变量名 | 默认值 | 必填 | 说明 |
|------|------|------|------|
| `VITE_API_PROXY_TARGET` | `http://127.0.0.1:24041` | 否 | 开发环境 API 代理目标地址 |

> 注：前端开发服务器默认运行在端口 `24043`，可在 `frontend/vite.config.js` 中修改。

## 3. 推荐配置

### 3.1 本地开发（`backend/.env`）

```env
APP_HOST=0.0.0.0
APP_PORT=24041
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./data/myharbor.dev.db
JWT_SECRET=dev-only-secret-change-me
JWT_EXPIRE_HOURS=24
CHECK_TIMEOUT_SECONDS=5
ENABLE_SCHEDULER=true
```

前端开发环境（`frontend/.env.development`）：

```env
VITE_API_PROXY_TARGET=http://127.0.0.1:24041
```

### 3.2 生产环境（Docker Compose 示例）

生产环境最重要的是设置强 `JWT_SECRET`，并确保数据目录持久化（如 `./data:/app/data`）。

## 4. 安全要求

- 生产环境必须设置强随机 `JWT_SECRET`（至少 32 字符）。
- `.env`、`backend/.env` 等本地配置文件不应提交到仓库（见 `.gitignore`）。
- 敏感配置建议通过 CI/CD Secret 或容器编排平台注入。

## 5. 校验建议

- 服务启动时打印关键配置摘要（脱敏后）。
- 对关键变量做启动校验（例如 `JWT_SECRET` 长度）。

## 6. 端口配置快速参考

### 6.1 默认端口

- **后端服务**：`24041`
- **前端开发服务器**：`24043`

### 6.2 修改端口

**方式一：通过环境变量（推荐）**

后端：
```bash
export APP_PORT=8080
# 或在 .env 文件中
APP_PORT=8080
```

前端：
```bash
export VITE_API_PROXY_TARGET=http://127.0.0.1:8080
# 或在 frontend/.env.development 中
VITE_API_PROXY_TARGET=http://127.0.0.1:8080
```

**方式二：修改配置文件**

后端：修改 `backend/app/config.py` 中的 `app_port` 默认值

前端：修改 `frontend/vite.config.js` 中的 `port` 和 `proxyTarget` 默认值

### 6.3 Docker 部署端口映射

在 `docker-compose.yml` 中修改端口映射：

```yaml
ports:
  - "24041:24041"  # 格式：宿主机端口:容器端口
```

如果修改了容器内端口（通过 `APP_PORT` 环境变量），需要同步修改映射：

```yaml
environment:
  - APP_PORT=8080
ports:
  - "24041:8080"  # 宿主机仍用 24041，容器内用 8080
```
