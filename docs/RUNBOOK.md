# MyHarbor 运维手册（Runbook）

## 1. 适用范围

- 适用于 MyHarbor 单实例部署（Docker / Docker Compose）。
- 覆盖启动、升级、备份恢复、故障排查和应急操作。

## 2. 部署前检查

1. 服务器已安装 Docker 与 Docker Compose。
2. 已准备持久化目录（如 `./data`）。
3. 已配置生产环境变量（至少 `JWT_SECRET`）。
4. 已开放服务端口（默认 24041）。

## 3. 启动与停止

### 3.1 启动

```bash
docker compose up -d --build
```

### 3.2 查看状态

```bash
docker compose ps
docker compose logs -f
```

### 3.3 停止

```bash
docker compose down
```

## 4. 升级流程

1. 备份当前数据（数据库和导出文件）。
2. 拉取新代码。
3. 执行镜像重建与重启：

```bash
docker compose up -d --build
```

4. 执行冒烟验证：
   - 首页可访问
   - 管理端可登录
   - 站点列表可读写
5. 观察日志 10 分钟无异常后完成升级。

## 5. 备份与恢复

### 5.1 在线备份（推荐）

- 调用管理接口：`GET /api/backup/export`
- 产出文件示例：`myharbor-backup-YYYYMMDD.json`

### 5.2 文件级备份

- 备份 `data/` 目录下 SQLite 文件与附件（如有）。

### 5.3 恢复

1. 通过接口导入：`POST /api/backup/import`
2. 选择策略：
   - `skip`：重复 URL 跳过
   - `overwrite`：重复 URL 覆盖
3. 导入后验证站点总数与关键配置。

## 6. 账号与路由应急

### 6.1 重置管理员

```bash
python backend/manage.py reset-admin
```

### 6.2 查看管理员

```bash
python backend/manage.py show-admin
```

### 6.3 查看后台路由码

```bash
python backend/manage.py show-route
```

### 6.4 设置管理员

```bash
python backend/manage.py set-admin --username <name> --password <pass>
```

## 7. 常见故障排查

### 7.1 无法登录后台

- 检查是否命中限流（`429`）。
- 检查 Token 是否过期（24 小时）。
- 使用 `show-route` 确认后台路由码。

### 7.2 站点状态一直离线

- 检查目标 URL 是否可达。
- 检查超时配置 `CHECK_TIMEOUT_SECONDS`。
- 检查检测任务日志是否报错。

### 7.3 统计数据异常

- 检查 `visit_log` 是否有数据。
- 检查日聚合任务是否执行。
- 手动触发聚合并复核 `visit_stats`。

### 7.4 数据库锁冲突

- 确认 SQLite 已启用 WAL。
- 避免高频并发写操作叠加。
- 将批处理任务错峰执行。

## 8. 监控建议

- 关注指标：
  - 接口 5xx 比例
  - 登录失败率
  - 定时任务成功率
  - 平均检测耗时
- 关注日志关键字：
  - `auth failed`
  - `rate limited`
  - `scheduler error`
  - `db locked`

## 9. 应急回滚

1. 停止当前版本容器。
2. 切换到上一个稳定版本镜像/代码。
3. 恢复最近可用备份。
4. 启动并执行冒烟检查。
5. 记录事故与根因，补充修复任务。
