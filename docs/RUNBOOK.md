# MyHarbor 运维手册（Runbook）

> 适用：单实例部署（Docker / Docker Compose / 1Panel），数据库默认使用 SQLite。

## 1. 关键约定（先看）

- **服务端口**：默认 `24041`
- **数据持久化**：宿主机 `./data` → 容器 `/app/data`
  - 默认数据库文件：`./data/myharbor.db`（容器内：`/app/data/myharbor.db`）
- **健康检查**：`GET /api/health`
- **后台入口（安全路由码）**：
  - 正常流程：先访问 `http://<HOST>:24041/{安全路由码}` → 自动跳转到 `/admin/login`
  - 直访 `http://<HOST>:24041/admin/login`：会返回 `404`（需要先走安全路由码“开门”）

> 注：本 Runbook 面向生产/部署环境（后端提供前端静态资源）。本地开发使用 Vite（`24043`）时，`/admin/login` 的行为可能不同。

## 2. 部署前检查

1. 服务器已安装 Docker 与 Docker Compose（或 1Panel 已内置 Docker 环境）。
2. 已准备持久化目录（例如项目目录下的 `./data`）。
3. **已设置生产环境 `JWT_SECRET`**（强随机，建议 ≥ 32 位）。
4. 已开放服务端口（默认 `24041`），或已配置反向代理到该端口。

## 3. 部署方式

### 3.1 方式 A：使用镜像部署（推荐）

适合：生产/测试环境、1Panel 部署、无需在服务器保留源码。

#### 3.1.1 Docker Compose（命令行）

建议使用版本号 tag（便于回滚），例如 `0.1.0-beta.1`：

```bash
# 进入存放 compose 文件的目录（包含 data/）
mkdir -p data && chmod 755 data

# 指定版本 + JWT_SECRET 后启动
MYHARBOR_TAG=0.1.0-beta.1 JWT_SECRET='<your-strong-secret>' \
  docker compose -f docker-compose.ghcr.yml up -d

# 查看状态/日志
docker compose -f docker-compose.ghcr.yml ps
docker compose -f docker-compose.ghcr.yml logs -f --tail 200
```

#### 3.1.2 1Panel（图形化）

1Panel 在“拉取镜像”阶段**可能不会解析** `image:` 中的 `${VAR}`，建议直接写死 tag：

- 把 `image:` 改成：`ghcr.io/imshonechen/myharbor:0.1.0-beta.1`（或 `:latest`）
- `JWT_SECRET` 也建议直接填具体值（不要写 `${JWT_SECRET:-...}`）

然后在 1Panel 的 Compose/编排界面保存并重建（重新部署）。

### 3.2 方式 B：源码构建部署（适合自定义开发/私有修改）

```bash
mkdir -p data && chmod 755 data
docker compose up -d --build
docker compose ps
docker compose logs -f --tail 200
```

## 4. 启动后验收（冒烟）

1. 健康检查：

```bash
curl -f http://127.0.0.1:24041/api/health
```

2. 获取后台安全路由码：见「7. 账号与路由应急」的 `show-route`。
3. 访问前台首页：`http://<HOST>:24041/`
4. 访问后台：先打开 `http://<HOST>:24041/{安全路由码}`（会跳转到 `/admin/login`）
5. 首次登录后立刻修改默认密码（默认：`admin/admin123`）。

## 5. 升级与回滚

### 5.1 升级（镜像部署）

1. 备份（见「6. 备份与恢复」）。
2. 将 compose 中的 `image:` tag 改为新版本（例如从 `0.1.0-beta.1` → `0.1.0`）。
3. 拉取并重启：

```bash
docker compose -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.ghcr.yml up -d
```

### 5.2 升级（源码构建部署）

```bash
git pull
docker compose up -d --build
```

### 5.3 回滚

- 镜像部署：把 `image:` tag 改回旧版本 → `pull` → `up -d`
- 必要时恢复备份（数据库文件级恢复或在线备份导入）。

## 6. 备份与恢复

### 6.1 在线备份（推荐，逻辑备份）

- 管理接口：`GET /api/backup/export`（需要 `Authorization: Bearer <token>`）
- 产出文件示例：`myharbor-backup-YYYYMMDD.json`

> 实操建议：直接在后台界面导出/导入（前端已集成备份入口）。

### 6.2 文件级备份（物理备份）

- 备份 `./data/` 目录（至少包含 `myharbor.db`；若启用了 WAL，还会有 `*.db-wal`、`*.db-shm`）。
- 保守做法：备份前先停服务，避免备份过程中写入导致不一致：

```bash
docker compose -f docker-compose.ghcr.yml down
tar -czf myharbor-data-$(date +%Y%m%d).tar.gz data/
docker compose -f docker-compose.ghcr.yml up -d
```

### 6.3 恢复

- 在线恢复：`POST /api/backup/import`（multipart 上传文件）
  - `strategy=skip`：重复 URL 跳过
  - `strategy=overwrite`：重复 URL 覆盖
- 文件级恢复：停服务 → 替换 `./data/` → 启动 → 冒烟验证。

## 7. 账号与路由应急

### 7.1 在容器内执行（推荐：镜像/1Panel 部署通用）

```bash
# 查看当前后台安全路由码（会输出完整访问地址）
docker exec -it myharbor python manage.py show-route

# 查看管理员用户名
docker exec -it myharbor python manage.py show-admin

# 重置管理员账号为默认（admin/admin123）
docker exec -it myharbor python manage.py reset-admin

# 设置管理员账号密码
docker exec -it myharbor python manage.py set-admin --username <name> --password <pass>
```

> 1Panel：进入容器 `myharbor` 的“终端/Exec”，直接执行 `python manage.py show-route` 即可。

### 7.2 在源码目录执行（仅源码部署）

```bash
python backend/manage.py show-route
python backend/manage.py show-admin
python backend/manage.py reset-admin
python backend/manage.py set-admin --username <name> --password <pass>
```

### 7.3 常见“进不去后台”说明

- 访问 `/admin/login` 返回 `404`：这是预期行为；先用 `show-route` 获取路由码并访问 `/{安全路由码}`。
- 修改了安全路由码后：需要重新访问 `/{新路由码}` 才能进入后台（旧路由码/旧 Cookie 会失效）。

## 8. 常见故障排查

### 8.1 镜像拉取失败（尤其是国内网络）

- 先在服务器上直接验证：`docker pull ghcr.io/imshonechen/myharbor:0.1.0-beta.1`
- 若出现 `timeout` / `TLS handshake timeout`：多为网络链路问题（GHCR 在国内可能不稳定）
  - 可选方案：将镜像同步到阿里云 ACR / 私有仓库，再从 ACR 拉取

### 8.2 无法登录后台

- 检查是否命中登录限流（`429`）。
- Token 有效期默认 24 小时，过期需重新登录。
- 若提示“找不到入口”：使用 `show-route` 确认安全路由码，按 `/{安全路由码}` 进入。

### 8.3 站点状态一直离线

- 检查目标 URL 是否可达（服务器到目标站点的网络是否通）。
- 检查超时配置 `CHECK_TIMEOUT_SECONDS`。
- 查看日志中是否有检测异常。

### 8.4 统计数据异常 / 没有更新

- 确认是否启用了调度器：环境变量 `ENABLE_SCHEDULER`（默认 `true`）。
- 查看日志中是否出现 `Scheduler started.` 或相关报错。
- 必要时可在容器内手动执行一次聚合（会写库，谨慎使用）：

```bash
docker exec -it myharbor python -c "from app.services.scheduler import run_visit_aggregation_job; print(run_visit_aggregation_job())"
```

### 8.5 数据库锁冲突（SQLite）

SQLite 在高并发写入/长事务时可能出现锁冲突（`database is locked`）：

- 确保只跑**单实例**（不要多副本共享同一个 `./data/myharbor.db`）。
- 将批处理任务错峰执行（检测/聚合/导入导出不要同时压测）。
- **可选：开启 WAL 模式**提升并发读写能力（会生成 `*.db-wal`、`*.db-shm` 文件，记得一并持久化/备份）：

```bash
docker exec -it myharbor python - <<'PY'
import sqlite3
db = "/app/data/myharbor.db"
conn = sqlite3.connect(db)
print("journal_mode(before):", conn.execute("PRAGMA journal_mode").fetchone()[0])
print("journal_mode(set):", conn.execute("PRAGMA journal_mode=WAL").fetchone()[0])
conn.close()
PY
```

## 9. 监控建议

- 关键检查：
  - `GET /api/health` 返回 `{"status":"ok","database":"ok"}`
  - 容器健康检查状态（`docker ps` / 1Panel 容器健康状态）
- 建议关注：接口 5xx、登录失败率、站点检测耗时、调度任务异常日志。
