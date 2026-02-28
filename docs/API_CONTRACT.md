# MyHarbor API 契约文档

## 1. 目的

- 作为前后端联调的接口契约基线。
- 约束请求字段、响应结构、错误码与鉴权规则。
- 与 `docs/TECH.md` 保持一致，如冲突以本文件为联调基线。

## 2. 通用约定

- Base URL：`/api`
- Content-Type：`application/json`
- 文件上传：`multipart/form-data`
- 时间格式：ISO8601
- 鉴权头：`Authorization: Bearer <token>`

统一响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

错误响应（当前实现）：

- 使用 HTTP 状态码表达错误类型。
- 响应体通常为 FastAPI 默认格式 `{"detail": ...}`（参数校验失败时 `detail` 为数组）。
- 登录限流返回 HTTP `429`，并带 `Retry-After` 响应头（秒）。

> 说明：如需业务错误码（例如 1001/1002/...），应通过后端全局异常处理器统一封装；当前实现未返回该字段。

## 3. 数据结构

### 3.1 Site

```json
{
  "id": 1,
  "name": "Docs",
  "url": "https://docs.example.com",
  "logo": null,
  "description": "文档站点",
  "tags": "工具,文档",
  "tags_list": ["工具", "文档"],
  "is_public": true,
  "status": "online",
  "sort_order": 10,
  "last_check_time": "2026-02-16T09:30:00+08:00",
  "created_at": "2026-02-16T09:00:00+08:00",
  "updated_at": "2026-02-16T09:30:00+08:00"
}
```

### 3.2 登录响应

```json
{
  "token": "<jwt>",
  "expires_at": "2026-02-17T10:00:00+08:00",
  "username": "admin"
}
```

## 4. 接口列表

### 4.1 公共接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/config/public` | 获取公开配置 |
| GET | `/sites/public` | 获取公开站点 |
| POST | `/visit` | 记录首页访问 |
| POST | `/visit/{site_id}` | 记录站点点击 |

### 4.2 管理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录 |
| GET | `/auth/me` | 获取当前用户信息 |
| GET | `/sites` | 全量站点查询 |
| POST | `/sites` | 新增站点 |
| PUT | `/sites/{site_id}` | 更新站点 |
| DELETE | `/sites/{site_id}` | 删除站点 |
| PATCH | `/sites/{site_id}/toggle` | 切换公开状态 |
| PUT | `/sites/sort` | 批量更新排序 |
| POST | `/sites/{site_id}/check` | 检测单站点 |
| POST | `/sites/check-all` | 检测全部站点 |
| GET | `/sites/{site_id}/status-logs` | 获取状态日志 |
| GET | `/sites/logo` | 根据站点网址自动获取 Logo |
| GET | `/stats/overview` | 统计概览 |
| GET | `/stats/sites` | 站点排行 |
| GET | `/stats/trend` | 趋势数据 |
| GET | `/config` | 获取系统配置 |
| PUT | `/config` | 更新系统配置 |
| GET | `/backup/export` | 导出备份 |
| POST | `/backup/import` | 导入备份 |

## 5. 关键接口细节

### 5.1 GET `/health`

说明：系统健康检查接口。

响应格式（不遵循统一响应格式）：

```json
{
  "status": "ok",
  "database": "ok"
}
```

状态值：
- `status`: `ok` 或 `degraded`
- `database`: `ok` 或 `error`

### 5.2 POST `/auth/login`

请求：

```json
{
  "username": "admin",
  "password": "admin123"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "token": "<jwt>",
    "expires_at": "2026-02-17T10:00:00+08:00",
    "username": "admin"
  }
}
```

### 5.3 GET `/auth/me`

说明：获取当前登录用户信息。

认证：需要 `Authorization: Bearer <token>` 头。

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "username": "admin"
  }
}
```

### 5.4 POST `/sites`

请求：

```json
{
  "name": "Docs",
  "url": "https://docs.example.com",
  "logo": "",
  "description": "文档站点",
  "tags": ["工具", "文档"],
  "is_public": true,
  "sort_order": 10
}
```

参数校验：

- `name`：1~100
- `url`：必须 `http://` 或 `https://`
- `tags`：最多 20 个

### 5.5 PUT `/config`

请求示例：

```json
{
  "site_title": "MyHarbor",
  "site_description": "欢迎来到 MyHarbor",
  "admin_route_code": "a3x9k2b1",
  "check_interval": 5
}
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "updated": true,
    "new_route_code": "a3x9k2b1",
    "relogin_required": false
  }
}
```

注意：
- 若 `new_route_code` 非空，前端需立刻跳转新后台路径
- 若 `relogin_required` 为 true，需要重新登录

### 5.6 POST `/visit`

说明：记录首页访问。

认证：无需认证。

请求：无请求体。

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "recorded": true
  }
}
```

### 5.7 POST `/visit/{site_id}`

说明：记录站点点击。

认证：无需认证。

路径参数：
- `site_id`：站点ID

请求：无请求体。

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "recorded": true
  }
}
```

错误响应（站点不存在）：

```json
{
  "detail": "site not found"
}
```

### 5.8 POST `/backup/import`

表单字段：

- `file`: JSON 文件
- `strategy`: `skip` 或 `overwrite`

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total": 20,
    "created": 12,
    "updated": 6,
    "skipped": 2
  }
}
```

### 5.9 GET `/sites/logo`

说明：根据站点网址自动解析站点图标（favicon / apple-touch-icon / manifest icons），用于快速填充站点的 `logo` 字段。

认证：需要 `Authorization: Bearer <token>` 头。

Query 参数：

- `url`：站点网址，必须以 `http://` 或 `https://` 开头。

成功响应（找到图标）：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "logo_url": "https://douyin.com/favicon.ico"
  }
}
```

成功响应（未找到/不符合要求）：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "logo_url": null
  }
}
```

错误响应：

- `200` 但 `logo_url` 为 `null`：未获取到合格图标（例如仅解析到长方形图标，长宽比不接近正方形会被过滤）
- `400`：`url` 非法（不是 http/https）

```json
{
  "detail": "url must start with http:// or https://"
}
```

## 6. 联调规则

- 接口新增字段时必须保持向后兼容（不删除旧字段）。
- 枚举值变更需同步更新前端常量与本契约文档。
- 任一接口结构变更需在 PR 里注明影响范围与回归点。
