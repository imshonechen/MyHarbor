# MyHarbor 技术设计文档

## 1. 文档目标

本文档基于 `docs/PRD.md`，给出 MyHarbor 的技术实现方案，用于指导开发、联调、测试与部署。范围覆盖：

- 系统架构与模块划分
- 数据模型与持久化策略
- API 设计与鉴权机制
- 定时任务与后台作业
- 部署、配置、测试、运维方案

## 2. 系统架构

### 2.1 总体架构

采用前后端分离开发、单服务部署模式：

- 前端：Vue 3 + Vite + TailwindCSS + vue-i18n，构建产物由后端静态托管
- 后端：FastAPI 提供 REST API + 静态资源服务
- 数据层：SQLite（SQLAlchemy ORM）
- 后台任务：进程内调度器（APScheduler）
- 国际化：vue-i18n v11，默认中文，支持中英文切换

逻辑分层：

- `routers`：接口路由层，参数校验、鉴权、响应封装
- `services`：业务层，状态检测、统计聚合、备份导入导出
- `models`：数据模型层，ORM 映射与关系定义
- `utils`：安全、限流、通用工具
- `locales`：国际化语言文件（中文、英文）

### 2.2 请求流程

1. 前端请求 API。
2. FastAPI 路由完成参数校验与权限判断。
3. 业务逻辑在 service 执行并读写数据库。
4. 返回统一 JSON 响应结构。
5. 前端根据响应更新界面状态。

## 3. 项目目录

```text
MyHarbor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 应用配置
│   │   ├── database.py          # 数据库连接
│   │   ├── models.py            # SQLAlchemy 模型
│   │   ├── schemas.py           # Pydantic 请求/响应模型
│   │   ├── dependencies/        # 依赖注入
│   │   │   └── auth.py          # 认证依赖
│   │   ├── routers/
│   │   │   ├── auth.py          # 认证接口
│   │   │   ├── sites.py         # 站点 CRUD 接口
│   │   │   ├── stats.py         # 访问统计接口
│   │   │   ├── config.py        # 系统配置接口
│   │   │   ├── public.py        # 公开接口
│   │   │   └── health.py        # 健康检查接口
│   │   ├── services/
│   │   │   ├── site_checker.py  # 站点状态检测
│   │   │   ├── stats_service.py # 统计聚合服务
│   │   │   ├── scheduler.py     # 定时任务
│   │   │   └── bootstrap.py     # 启动初始化
│   │   └── utils/
│   │       ├── security.py      # 密码哈希、JWT 工具
│   │       └── rate_limiter.py  # 登录限流
│   ├── tests/                   # 测试文件
│   ├── manage.py                # CLI 管理脚本
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── locales/             # 国际化语言文件
│   │   │   ├── index.js         # i18n 配置
│   │   │   ├── zh-CN.js         # 中文翻译
│   │   │   └── en.js            # 英文翻译
│   │   ├── router/
│   │   │   └── index.js         # Vue Router 配置
│   │   ├── layouts/
│   │   │   └── AdminLayout.vue  # 后台布局（侧边栏导航）
│   │   ├── views/
│   │   │   ├── HomeView.vue     # 前台首页
│   │   │   └── admin/           # 后台页面模块
│   │   │       ├── LoginView.vue      # 登录页
│   │   │       ├── DashboardView.vue  # 仪表盘
│   │   │       ├── SitesView.vue      # 站点管理
│   │   │       ├── StatisticsView.vue # 访问统计
│   │   │       ├── MonitoringView.vue # 站点监控
│   │   │       └── SettingsView.vue   # 系统设置
│   │   ├── components/          # 公共组件
│   │   │   ├── SiteFormDrawer.vue   # 站点表单抽屉
│   │   │   └── ConfirmDialog.vue    # 确认对话框
│   │   ├── api/                 # API 请求封装
│   │   │   ├── client.js        # Axios 客户端
│   │   │   ├── auth.js
│   │   │   ├── sites.js
│   │   │   ├── stats.js
│   │   │   ├── config.js
│   │   │   └── public.js
│   │   ├── App.vue              # 根组件
│   │   ├── main.js              # 入口文件
│   │   └── styles.css           # 全局样式
│   ├── dist/                    # 构建产物
│   ├── package.json
│   ├── vite.config.js
│   ├── postcss.config.js
│   └── tailwind.config.js
├── docker-compose.yml
├── Dockerfile
└── docs/
    ├── PRD.md
    ├── TECH.md
    ├── API_CONTRACT.md
    ├── CODING_RULES.md
    ├── ENV.md
    ├── I18N.md
    ├── DB_MIGRATIONS.md
    ├── TEST_CASES.md
    ├── TASKS.md
    ├── ROADMAP.md
    └── RUNBOOK.md
```

## 4. 数据库设计

### 4.1 表设计

#### site

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `name` TEXT NOT NULL
- `url` TEXT NOT NULL UNIQUE
- `logo` TEXT NULL
- `description` TEXT NULL
- `tags` TEXT NULL
- `is_public` BOOLEAN NOT NULL DEFAULT 1
- `status` TEXT NOT NULL DEFAULT 'unknown'
- `sort_order` INTEGER NOT NULL DEFAULT 9999
- `last_check_time` DATETIME NULL
- `created_at` DATETIME NOT NULL
- `updated_at` DATETIME NOT NULL

约束：

- `status` 仅允许 `online/offline/unknown`

#### site_config

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `key` TEXT NOT NULL UNIQUE
- `value` TEXT NOT NULL

#### site_status_log

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `site_id` INTEGER NOT NULL
- `status` TEXT NOT NULL
- `response_time` INTEGER NULL
- `checked_at` DATETIME NOT NULL

外键：

- `site_id -> site.id ON DELETE CASCADE`

#### visit_log

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `site_id` INTEGER NULL
- `ip` TEXT NULL
- `user_agent` TEXT NULL
- `visited_at` DATETIME NOT NULL

外键：

- `site_id -> site.id ON DELETE CASCADE`

#### visit_stats

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `site_id` INTEGER NULL
- `date` DATE NOT NULL
- `click_count` INTEGER NOT NULL DEFAULT 0

外键：

- `site_id -> site.id ON DELETE CASCADE`

唯一约束：

- `UNIQUE(site_id, date)`（保证聚合幂等）

### 4.2 索引建议

- `site(is_public, sort_order)`
- `site(tags)`
- `site_status_log(site_id, checked_at)`
- `visit_log(site_id, visited_at)`
- `visit_stats(site_id, date)`
- `site_config(key)`（唯一索引）

### 4.3 初始化策略

启动时执行：

1. 自动建表（`Base.metadata.create_all`）。
2. 若 `site_config` 无数据，写入默认配置：
   - `site_title`、`site_description`、`copyright`
   - `icp_number`
   - `admin_username`
   - `admin_password`（哈希存储）
   - `admin_route_code`（随机 8 位字母数字）
   - `check_interval`
3. 启动日志打印后台入口（包含 route code）。

## 5. 后端设计

### 5.1 配置管理（`config.py`）

通过环境变量覆盖默认配置（详见 `docs/ENV.md`）：

- `APP_NAME`（默认 `MyHarbor API`）
- `APP_HOST`（默认 `0.0.0.0`）
- `APP_PORT`（默认 `24041`）
- `LOG_LEVEL`（默认 `INFO`）
- `DATABASE_URL`（默认 `sqlite:///./data/myharbor.db`）
- `JWT_SECRET`（生产必须设置）
- `JWT_EXPIRE_HOURS`（默认 `24`）
- `CHECK_TIMEOUT_SECONDS`（默认 `5`）
- `ENABLE_SCHEDULER`（默认 `true`）

> 站点检测“间隔（分钟）”属于系统配置 `check_interval`（默认 5），可通过 `PUT /api/config` 修改，不是环境变量。

### 5.2 鉴权与安全

- 登录：`POST /api/auth/login`，用户名密码校验通过后签发 JWT
- JWT：
  - 算法：`HS256`
  - 载荷：`sub`（用户名）、`exp`（过期时间）
  - 有效期：24 小时
- 密码存储：PBKDF2-SHA256（`pbkdf2_sha256`）哈希（见 `backend/app/utils/security.py`）
- 登录限流：
  - 同 IP 每分钟最多 5 次
  - 超过后锁定 15 分钟
  - 可使用内存字典（单实例）或 SQLite 表（重启可恢复）
- 后台入口保护：
  - 路由前缀为动态 `/{admin_route_code}`
  - 修改后返回新路由码，前端自动跳转新路径

### 5.3 核心服务

#### site_checker.py

- 使用 `httpx.Client` 发起检测请求
- 超时 5 秒
- 结果判定：
  - 2xx/3xx/4xx（< 500）：`online`（服务器在线，包括 403/404 等）
  - 5xx（>= 500）：`offline`（服务器错误）
  - 异常、超时：`offline`（无法连接）
- 判定说明：
  - 4xx 状态码（如 403 Forbidden）表示服务器在线但拒绝访问
  - 常见于 Cloudflare 防护、需要登录、IP 限制等场景
  - 只有服务器错误（5xx）或连接异常才判定为 offline
- 落库逻辑：
  - 更新 `site.status`、`site.last_check_time`
  - 新增 `site_status_log`

#### stats_service.py

- 负责按天聚合 `visit_log -> visit_stats`
- 提供统计查询：
  - 总览（日/月/年/总计）
  - 站点排行（日/月/年/总计）
  - 30 天趋势

#### scheduler.py

定时任务：

- 站点检测：按 `check_interval` 执行全量检测
- 日聚合：每天 00:05 聚合前一日访问日志
- 日清理：每天 00:30 清理过期日志
  - `site_status_log` 保留 30 天
  - `visit_log` 保留 90 天

### 5.4 API 约定

统一响应格式建议：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

错误码建议：

- `400` 参数错误
- `401` 未认证/Token 失效
- `403` 无权限
- `404` 资源不存在
- `409` 资源冲突（如 URL 重复）
- `429` 登录限流
- `500` 服务内部异常

### 5.5 备份与导入

`GET /api/backup/export`：

- 导出 JSON，包含 `sites` + 可选 `config`（排除敏感字段）

`POST /api/backup/import`：

- 上传 JSON
- 重复 URL 处理策略：
  - `skip`：跳过
  - `overwrite`：覆盖原有站点信息
- 整体导入事务提交，失败回滚

## 6. 前端设计

### 6.1 页面与路由

- `/`：前台首页
- `/{routeCode}`：后台登录页与管理页入口
- 管理页子模块：
  - 站点管理
  - 访问统计
  - 系统设置

路由守卫：

- 管理路由需 JWT
- Token 过期跳转登录
- 路由码变化后更新本地路由状态

### 6.2 状态管理

- `auth store`：Token、登录态、用户信息
- `theme store`：亮暗模式（默认跟随系统，支持用户切换）
- 站点筛选状态：标签、关键词、公开状态等

### 6.3 关键交互

- 首页：
  - 标签筛选 + 名称搜索（可组合）
  - 点击卡片先调用访问记录接口，再新标签页跳转
- 后台站点列表：
  - 支持拖拽排序（更新 `sort_order` 批量提交）
  - 快捷切换公开状态
  - 手动检测单站点/全站点
- 状态图例（30 天）：
  - 颜色映射：绿/红/灰
  - hover 展示时间与响应时延

### 6.4 国际化（i18n）

**技术方案：**
- 使用 vue-i18n v11 实现多语言支持
- 默认语言：中文（zh-CN）
- 支持语言：中文、英文

**实现细节：**
- 语言文件位置：`frontend/src/locales/`
  - `index.js`：i18n 配置
  - `zh-CN.js`：中文翻译（120+ 条）
  - `en.js`：英文翻译（120+ 条）
- 语言切换：管理后台侧边栏底部提供切换按钮
- 语言持久化：用户选择保存在 localStorage
- 翻译覆盖：所有界面文本、按钮、提示、错误消息

**使用方式：**
```vue
<script setup>
import { useI18n } from 'vue-i18n'
const { t, locale } = useI18n()
</script>

<template>
  <h1>{{ t('dashboard.title') }}</h1>
  <button @click="locale = 'en'">Switch to English</button>
</template>
```

**翻译键结构：**
- `common.*`：通用文本（按钮、状态等）
- `home.*`：首页
- `login.*`：登录页
- `layout.*`：后台布局
- `dashboard.*`：仪表盘
- `sites.*`：站点管理
- `siteForm.*`：站点表单
- `settings.*`：系统设置
- `statistics.*`：访问统计
- `monitoring.*`：站点监控

详细文档参见：`docs/I18N.md`

## 7. 非功能实现

### 7.1 性能

- SQLite 开启 WAL 模式提升并发读写
- 检测任务异步并发（设置合理并发上限，如 10）
- 列表查询分页（预留能力，初版可不开放分页参数）

### 7.2 可观测性

- 结构化日志（JSON 或统一文本格式）
- 关键日志点：
  - 启动初始化
  - 登录成功/失败（不记录明文密码）
  - 定时任务执行结果
  - 导入导出结果

### 7.3 稳定性

- 导入、批量更新、聚合任务使用数据库事务
- 定时任务异常隔离，不影响主 API 服务
- 所有外部 HTTP 请求设置超时与异常兜底

## 8. 部署方案

### 8.1 Dockerfile（建议）

多阶段构建：

1. 前端阶段：Node 镜像打包 `frontend/dist`
2. 后端阶段：Python 镜像安装依赖
3. 复制前端 dist 到后端静态目录
4. 启动 FastAPI（`uvicorn app.main:app`）

### 8.2 docker-compose.yml（建议）

- 单服务 `myharbor`
- 端口映射：`24041:24041`
- 卷挂载：`./data:/app/data`
- 环境变量注入：`JWT_SECRET`、数据库路径、端口等
- 重启策略：`unless-stopped`

## 9. CLI 管理脚本

`backend/manage.py` 命令：

- `reset-admin`
- `show-admin`
- `show-route`
- `set-admin --username <name> --password <pass>`

实现要点：

- 直接访问 `site_config`
- 修改密码时统一走哈希函数
- 命令输出避免泄露敏感信息

## 10. 测试策略

### 10.1 后端测试

- 单元测试：
  - URL 校验
  - 登录限流
  - 状态判定逻辑
  - 聚合统计逻辑
- 集成测试：
  - 认证流程（登录、鉴权、过期）
  - 站点 CRUD + 级联删除
  - 手动检测与定时清理
  - 备份导入导出

### 10.2 前端测试

- 组件测试：
  - `SiteCard`、`TagFilter`、`UptimeBar`
- 端到端测试：
  - 首页浏览、筛选、点击跳转
  - 后台登录、增删改查、排序、设置修改

### 10.3 验收映射

- F1/F2/F3/F4/F5 功能逐条对应测试用例与接口断言
- NF1~NF8 对应部署、性能、清理策略与配置验证

## 11. 风险与约束

- SQLite 在高并发下存在写瓶颈，后续可迁移 PostgreSQL
- 进程内限流与调度器在多实例部署时需改为共享存储方案
- 动态后台路由只能降低扫描概率，不能替代标准安全措施

## 12. 里程碑建议

1. M1：基础框架 + 数据模型 + 公共接口
2. M2：后台认证 + 站点管理 + 系统设置
3. M3：状态检测 + 定时任务 + 30 天图例
4. M4：访问统计 + 备份恢复 + CLI + Docker 交付

## 13. 接口详细定义

### 13.1 通用协议

- Base URL：`/api`
- 认证方式：`Authorization: Bearer <JWT>`
- 请求体：默认 `application/json`；导入接口使用 `multipart/form-data`
- 字符编码：`UTF-8`
- 时间字段：ISO8601（示例：`2026-02-16T09:30:00+08:00`）

统一响应体：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

分页响应体（用于列表）：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "size": 20
  }
}
```

### 13.2 错误响应约定

- 成功响应：统一返回 `{"code":0,"message":"ok","data":...}`。
- 错误响应：当前由 FastAPI 默认异常格式返回，形如 `{"detail":"..."}`，并使用 HTTP 状态码表达错误类型。
- 登录限流：返回 HTTP `429`，并带 `Retry-After` 响应头（秒）。

> 如需业务错误码（例如 1001/1002/...）做精细化区分，应通过全局异常处理器统一封装；当前实现未返回该字段。

### 13.3 核心 DTO 定义

#### SiteDTO

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 站点 ID |
| name | string | 站点名称，1~100 字符 |
| url | string | 站点 URL，仅允许 `http/https` |
| logo | string/null | Logo URL 或静态路径，最长 2048 |
| description | string/null | 简介，最长 500 |
| tags | string | 逗号分隔标签（存储格式） |
| tags_list | string[] | 标签数组（响应便于前端展示） |
| is_public | boolean | 是否公开 |
| status | string | `online/offline/unknown` |
| sort_order | int | 排序权重（越小越靠前） |
| last_check_time | datetime/null | 最近检测时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

#### SiteCreateRequest

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| name | string | 是 | 1~100 |
| url | string | 是 | `http/https`，最长 2048 |
| logo | string | 否 | URL 或路径，最长 2048 |
| description | string | 否 | 最长 500 |
| tags | string[] | 否 | 单个标签 1~20，最多 20 个 |
| is_public | boolean | 否 | 默认 `true` |
| sort_order | int | 否 | 默认 `9999` |

#### SiteUpdateRequest

与 `SiteCreateRequest` 相同，字段均可选（至少传 1 个字段）。

#### ConfigPublicDTO

| 字段 | 类型 | 说明 |
|------|------|------|
| site_title | string | 页面标题 |
| site_description | string | 站点介绍（可多行） |
| copyright | string | 版权文案 |
| icp_number | string | ICP 信息 |

#### ConfigAdminDTO

`ConfigPublicDTO` + 以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| admin_username | string | 管理员用户名 |
| admin_route_code | string | 后台安全路由码 |
| check_interval | int | 状态检测间隔（分钟） |

#### LoginRequest / LoginResponse

请求：

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| username | string | 是 | 1~64 |
| password | string | 是 | 1~128 |

响应：

| 字段 | 类型 | 说明 |
|------|------|------|
| token | string | JWT Token |
| expires_at | datetime | 过期时间 |
| username | string | 当前登录用户 |

#### SiteStatusLogDTO

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 日志 ID |
| site_id | int | 站点 ID |
| status | string | `online/offline` |
| response_time | int/null | 响应时延（毫秒） |
| checked_at | datetime | 检测时间 |

#### StatsOverviewDTO

| 字段 | 类型 | 说明 |
|------|------|------|
| home | object | 首页访问统计 |
| sites_total | int | 全站点点击总数 |

`home` 对象：

| 字段 | 类型 | 说明 |
|------|------|------|
| day | int | 当日 |
| month | int | 当月 |
| year | int | 当年 |
| total | int | 总计 |

### 13.4 公共接口（无需认证）

#### 13.4.1 GET `/api/health`

说明：系统健康检查接口，用于监控和负载均衡器探测。

响应格式：

```json
{
  "status": "ok",
  "database": "ok"
}
```

状态说明：

- `status`: 系统整体状态
  - `ok`: 系统正常
  - `degraded`: 系统降级（数据库异常）
- `database`: 数据库连接状态
  - `ok`: 数据库连接正常
  - `error`: 数据库连接失败

注意：此接口不遵循统一响应格式，直接返回健康状态对象。

#### 13.4.2 GET `/api/config/public`

说明：获取首页展示配置。

响应 `data`：

```json
{
  "site_title": "MyHarbor",
  "site_description": "欢迎来到 MyHarbor",
  "copyright": "&copy; 2026 MyHarbor",
  "icp_number": ""
}
```

#### 13.4.3 GET `/api/sites/public`

说明：获取公开站点列表。

Query 参数：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 否 | 名称/简介模糊搜索 |
| tag | string | 否 | 按标签过滤 |

响应 `data`：

```json
{
  "items": [
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
      "last_check_time": "2026-02-16T09:30:00+08:00"
    }
  ],
  "total": 1
}
```

#### 13.4.4 POST `/api/visit`

说明：记录首页访问（`site_id = null`）。

请求体：无。

响应 `data`：

```json
{
  "recorded": true
}
```

#### 13.4.5 POST `/api/visit/{site_id}`

说明：记录站点点击。

Path 参数：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| site_id | int | 是 | 站点 ID |

响应 `data`：

```json
{
  "recorded": true
}
```

### 13.5 管理接口（需 JWT 认证）

说明：除 `POST /api/auth/login` 外，均需 `Authorization` 头。

#### 13.5.1 POST `/api/auth/login`

请求体：`LoginRequest`。

成功响应 `data`：

```json
{
  "token": "<jwt>",
  "expires_at": "2026-02-17T10:00:00+08:00",
  "username": "admin"
}
```

失败场景：

- 用户名或密码错误：HTTP `401`
- 达到限流阈值：HTTP `429`（响应头 `Retry-After`）

#### 13.5.1.1 GET `/api/auth/me`

说明：获取当前登录用户信息。

认证：需要 JWT Token。

成功响应 `data`：

```json
{
  "username": "admin"
}
```

失败场景：

- Token 无效或过期：HTTP `401`

#### 13.5.2 GET `/api/sites`

说明：获取全部站点（含隐藏站点）。

Query 参数：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 否 | 名称/URL 搜索 |
| tag | string | 否 | 标签过滤 |
| status | string | 否 | `online/offline/unknown` |
| is_public | bool | 否 | 公开状态 |
| page | int | 否 | 默认 1 |
| size | int | 否 | 默认 20，最大 100 |

响应：分页 `SiteDTO` 列表。

#### 13.5.3 POST `/api/sites`

说明：新增站点。

请求体：`SiteCreateRequest`。

成功响应：`data` 为新增后的 `SiteDTO`。

错误：

- URL 重复：HTTP `409`
- URL 非法：HTTP `422`

#### 13.5.4 PUT `/api/sites/{site_id}`

说明：更新站点。

Path 参数：`site_id`（站点 ID）。

请求体：`SiteUpdateRequest`。

成功响应：`data` 为更新后的 `SiteDTO`。

#### 13.5.5 DELETE `/api/sites/{site_id}`

说明：删除站点，并级联删除 `site_status_log/visit_log/visit_stats`。

成功响应 `data`：

```json
{
  "deleted": true
}
```

#### 13.5.6 PATCH `/api/sites/{site_id}/toggle`

说明：切换公开状态。

成功响应 `data`：

```json
{
  "id": 1,
  "is_public": false
}
```

#### 13.5.7 PUT `/api/sites/sort`

说明：批量更新排序权重。

请求体：

```json
{
  "items": [
    { "id": 1, "sort_order": 10 },
    { "id": 2, "sort_order": 20 }
  ]
}
```

响应 `data`：

```json
{
  "updated": 2
}
```

#### 13.5.8 POST `/api/sites/{site_id}/check`

说明：手动检测单个站点。

响应 `data`：

```json
{
  "site_id": 1,
  "status": "online",
  "response_time": 123,
  "checked_at": "2026-02-16T10:12:00+08:00"
}
```

#### 13.5.9 POST `/api/sites/check-all`

说明：手动批量检测全部站点。

响应 `data`：

```json
{
  "total": 15,
  "online": 12,
  "offline": 3,
  "checked_at": "2026-02-16T10:15:00+08:00"
}
```

#### 13.5.10 GET `/api/sites/{site_id}/status-logs`

说明：获取指定站点最近 30 天状态日志。

Query 参数：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| days | int | 否 | 默认 30，最大 30 |

响应 `data`：

```json
{
  "site_id": 1,
  "items": [
    {
      "status": "online",
      "response_time": 120,
      "checked_at": "2026-02-16T10:00:00+08:00"
    }
  ]
}
```

#### 13.5.11 GET `/api/stats/overview`

说明：获取首页与全站点击概览（日/月/年/总计）。

响应 `data`（示例）：

```json
{
  "home": { "day": 30, "month": 320, "year": 1200, "total": 5800 },
  "sites_total": 24000
}
```

#### 13.5.12 GET `/api/stats/sites`

说明：按点击量返回站点排行。

Query 参数：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| range | string | 否 | `day/month/year/total`，默认 `day` |
| limit | int | 否 | 默认 20，最大 100 |

响应 `data`：

```json
{
  "items": [
    { "site_id": 1, "site_name": "Docs", "click_count": 80 }
  ]
}
```

#### 13.5.13 GET `/api/stats/trend`

说明：获取近 N 天趋势。

Query 参数：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| days | int | 否 | 默认 30，最大 90 |

响应 `data`：

```json
{
  "items": [
    { "date": "2026-02-01", "home_count": 12, "site_click_count": 55 }
  ]
}
```

#### 13.5.14 GET `/api/config`

说明：获取系统配置（管理视角）。

响应 `data`：`ConfigAdminDTO`。

#### 13.5.15 PUT `/api/config`

说明：更新系统配置。

请求体：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| site_title | string | 否 | 页面标题 |
| site_description | string | 否 | 介绍文本 |
| copyright | string | 否 | 版权 |
| icp_number | string | 否 | ICP |
| admin_username | string | 否 | 新用户名 |
| admin_password | string | 否 | 新密码（后端哈希） |
| admin_route_code | string | 否 | 新安全路由码（6~32） |
| check_interval | int | 否 | 检测间隔分钟，范围 1~1440 |

响应 `data`：

```json
{
  "updated": true,
  "new_route_code": "a3x9k2b1"
}
```

说明：若 `new_route_code` 非空，前端需立刻跳转新后台路径。

#### 13.5.16 GET `/api/backup/export`

说明：导出站点数据。

响应：

- `Content-Type: application/json`
- 附件下载名：`myharbor-backup-YYYYMMDD.json`

导出 JSON 结构：

```json
{
  "version": "1.0",
  "exported_at": "2026-02-16T10:00:00+08:00",
  "sites": [],
  "config": {
    "site_title": "MyHarbor",
    "site_description": "欢迎来到 MyHarbor",
    "copyright": "&copy; 2026 MyHarbor",
    "icp_number": ""
  }
}
```

#### 13.5.17 POST `/api/backup/import`

说明：上传备份文件并批量导入。

表单参数：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | JSON 文件 |
| strategy | string | 否 | `skip/overwrite`，默认 `skip` |

响应 `data`：

```json
{
  "total": 20,
  "created": 12,
  "updated": 6,
  "skipped": 2
}
```

### 13.6 鉴权与 Header 约定

- 鉴权失败统一返回 HTTP `401`（响应体通常为 `{"detail":"..."}`）
- 建议返回头：
  - `X-Request-Id`：链路追踪 ID
  - `X-RateLimit-Remaining`：登录接口剩余次数
  - `Retry-After`：被限流后重试秒数

### 13.7 联调校验清单

- URL 必须是 `http://` 或 `https://`
- 标签输入在后端统一 `trim`，空值去除后再存储
- `sort_order` 数值越小越靠前
- 删除站点后，关联日志与统计必须同步删除
- 修改 `admin_route_code` 后，旧路径应立即失效
