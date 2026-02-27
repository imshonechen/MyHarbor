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
4. 成功时返回统一 JSON 响应结构；错误时返回 FastAPI 默认异常响应（`detail`）。
5. 前端根据响应更新界面状态。

## 3. 项目目录

```text
MyHarbor/
├── data/                    # 数据目录（SQLite：默认 `data/myharbor.db`；运行时生成，不提交仓库）
│   └── myharbor.db
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
│   │   │   ├── client.js        # API 客户端封装（fetch）
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
    ├── PRD.md                   # 产品需求文档（含路线图/任务/测试用例）
    ├── TECH.md                  # 技术设计文档（含环境变量/开发规范/i18n/迁移规范等）
    ├── API_CONTRACT.md          # API 契约文档（联调基线）
    └── RUNBOOK.md               # 运维手册（部署、升级、备份、故障排查）
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

通过环境变量覆盖默认配置（见本文附录「环境变量」或 `backend/app/config.py`）：

- `APP_NAME`（默认 `MyHarbor API`）
- `APP_HOST`（默认 `0.0.0.0`）
- `APP_PORT`（默认 `24041`）
- `LOG_LEVEL`（默认 `INFO`）
- `DATABASE_URL`（默认：项目根目录 `data/myharbor.db`）
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

详细说明见本文附录「多语言（i18n）」。

## 7. 非功能实现

### 7.1 性能

- 建议 SQLite 开启 WAL 模式提升并发读写（见 `docs/RUNBOOK.md` 的故障排查章节）。
- 站点检测当前为串行执行；如需加速可在 `check_all_sites` 引入并发与限流。
- 列表查询支持分页（`GET /api/sites` 的 `page/size` 参数）。

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

---

## 附录

> 为减少文档数量，原 `docs/ENV.md`、`docs/CODING_RULES.md`、`docs/I18N.md`、`docs/DB_MIGRATIONS.md` 的内容已合并至本附录（文件已删除）。

### 环境变量

> 环境变量真源为 `backend/app/config.py` 的 `Settings`。

#### 使用说明

- 后端配置由 `backend/app/config.py` 的 `Settings` 管理，可通过环境变量覆盖默认值。
- 本地开发（在 `backend/` 目录运行 uvicorn）时，可在 `backend/.env` 放置配置；生产/Docker 部署建议在容器编排层注入环境变量。
- 未配置时使用默认值（见下表）。
- 注意：站点检测**间隔**不是环境变量，属于系统配置 `check_interval`（分钟），可在管理后台“系统设置”里修改（对应接口 `PUT /api/config`）。

#### 环境变量清单

##### 后端环境变量

| 变量名 | 默认值 | 必填 | 说明 |
|------|------|------|------|
| `APP_NAME` | `MyHarbor API` | 否 | FastAPI 应用标题 |
| `APP_HOST` | `0.0.0.0` | 否 | 服务监听地址 |
| `APP_PORT` | `24041` | 否 | 后端服务端口 |
| `LOG_LEVEL` | `INFO` | 否 | 日志级别 |
| `DATABASE_URL` | 项目根目录 `data/myharbor.db` | 否 | 数据库连接串（默认指向项目根目录 `data/myharbor.db`） |
| `JWT_SECRET` | `myharbor-dev-secret-change-me` | 是（生产） | JWT 签名密钥（生产必须更换强随机值） |
| `JWT_EXPIRE_HOURS` | `24` | 否 | Token 有效期（小时） |
| `CHECK_TIMEOUT_SECONDS` | `5` | 否 | 状态检测超时时间（秒） |
| `ENABLE_SCHEDULER` | `true` | 否 | 是否启用内置调度器（检测/聚合/清理） |

##### 前端环境变量

| 变量名 | 默认值 | 必填 | 说明 |
|------|------|------|------|
| `VITE_API_PROXY_TARGET` | `http://127.0.0.1:24041` | 否 | 开发环境 API 代理目标地址 |

> 注：前端开发服务器默认运行在端口 `24043`，可在 `frontend/vite.config.js` 中修改。

#### 推荐配置

##### 本地开发（`backend/.env`）

```env
APP_HOST=0.0.0.0
APP_PORT=24041
LOG_LEVEL=DEBUG
# 可选：使用独立开发库（不配置则默认使用项目根目录 `data/myharbor.db`）
DATABASE_URL=sqlite:///../data/myharbor.dev.db
JWT_SECRET=dev-only-secret-change-me
JWT_EXPIRE_HOURS=24
CHECK_TIMEOUT_SECONDS=5
ENABLE_SCHEDULER=true
```

前端开发环境（`frontend/.env.development`）：

```env
VITE_API_PROXY_TARGET=http://127.0.0.1:24041
```

##### 生产环境（Docker Compose 提示）

生产环境最重要的是设置强 `JWT_SECRET`，并确保数据目录持久化（如 `./data:/app/data`）。

#### 安全要求

- 生产环境必须设置强随机 `JWT_SECRET`（至少 32 字符）。
- `.env`、`backend/.env` 等本地配置文件不应提交到仓库（见 `.gitignore`）。
- 敏感配置建议通过 CI/CD Secret 或容器编排平台注入。

#### 校验建议

- 服务启动时打印关键配置摘要（脱敏后）。
- 对关键变量做启动校验（例如 `JWT_SECRET` 长度）。

#### 端口配置快速参考

##### 默认端口

- **后端服务**：`24041`
- **前端开发服务器**：`24043`

##### 修改端口

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

- 后端：修改 `backend/app/config.py` 中的 `app_port` 默认值
- 前端：修改 `frontend/vite.config.js` 中的 `port` 和 `proxyTarget` 默认值

##### Docker 部署端口映射

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

### 开发规范

#### 目标

- 统一代码风格与目录结构。
- 降低协作成本，提升可维护性与可测试性。

#### 通用规范

- 变更必须附带明确目的，不提交无关改动。
- 业务逻辑优先放在 service 层，router 仅做校验和编排。
- 新增功能必须同时补充文档与测试。
- 禁止硬编码敏感信息（密码、密钥、Token）。

#### 后端规范（Python + FastAPI）

##### 目录职责

- `routers/`：参数校验、鉴权、调用 service、返回响应。
- `services/`：核心业务逻辑、事务边界。
- `models.py`：ORM 模型定义。
- `schemas.py`：Pydantic 请求/响应模型。
- `utils/`：通用工具，不依赖具体业务。

##### 编码要求

- 使用类型注解。
- 所有外部请求必须设置超时。
- 接口返回统一响应结构（成功场景）。
- 错误处理建议使用统一异常映射，不直接向前端暴露堆栈。

##### 命名规则

- 文件与函数：`snake_case`
- 类名：`PascalCase`
- 常量：`UPPER_SNAKE_CASE`

#### 前端规范（Vue 3）

- 页面放 `views/`，可复用组件放 `components/`。
- API 请求统一从 `api/` 发起，不在组件中直写 URL。
- 状态管理统一使用 store，避免跨组件隐式依赖。
- 组件 Props 和事件命名应语义化。

#### API 变更规范

- 改动接口时同步更新：
  - `docs/API_CONTRACT.md`
  - `docs/TECH.md`（如涉及架构/字段变更）
- 破坏性变更需在 PR 标注：
  - 影响范围
  - 升级步骤
  - 回滚方案

#### 数据库变更规范

- 禁止直接在线手改表结构。
- 所有表结构变更必须通过迁移脚本。
- 迁移脚本必须具备回滚能力。

#### Git 与提交规范

##### 分支命名

- `feature/<name>`
- `fix/<name>`
- `chore/<name>`
- `docs/<name>`

##### 提交信息

建议格式：

```text
类型(范围): 简要说明
```

推荐类型：

- `新功能`：新增功能
- `修复`：缺陷修复
- `文档`：文档更新
- `重构`：代码重构（不改行为）
- `测试`：测试相关
- `构建`：构建、依赖、脚本变更

示例：

```text
新功能(接口): 新增站点批量检测接口
修复(鉴权): 修复登录限流锁定时间判断错误
文档(技术文档): 补充 API 字段级契约说明
```

#### Code Review 检查项

1. 是否满足需求与 DoD。
2. 是否引入行为回归或安全风险。
3. 是否补充必要测试与文档。
4. 是否存在明显性能或并发问题。
5. 是否保证可读性与可维护性。

### 多语言（i18n）

#### 概述

MyHarbor 支持多语言功能，默认语言为**中文（简体）**，同时支持**英文**。用户可以在管理后台自由切换语言。

#### 已实现的功能

##### 多语言配置

- **默认语言**：中文（zh-CN）
- **支持语言**：中文、英文
- **语言持久化**：用户选择的语言会保存在浏览器的 localStorage 中，下次访问时自动应用

##### 语言文件位置

```text
frontend/src/locales/
├── index.js      # i18n 配置文件
├── zh-CN.js      # 中文翻译
└── en.js         # 英文翻译
```

#### 使用方法

##### 用户端使用

1. 访问前台首页：默认显示中文界面。
2. 登录管理后台。
3. 在左侧边栏底部切换语言（中文/EN），切换后立即生效并持久化。

##### 开发者使用

在组件中使用 i18n：

```vue
<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div>
    <h1>{{ t('dashboard.title') }}</h1>
  </div>
</template>
```

添加新的翻译：

1. 在 `frontend/src/locales/zh-CN.js` 中添加中文翻译。
2. 在 `frontend/src/locales/en.js` 中添加英文翻译。
3. 在组件中使用对应 key。

#### 翻译键结构

```text
common          - 通用文本（按钮、状态等）
home            - 首页
login           - 登录页
layout          - 后台布局
dashboard       - 仪表盘
sites           - 站点管理
siteForm        - 站点表单
settings        - 系统设置
statistics      - 访问统计
monitoring      - 站点监控
```

#### 注意事项

- 语言切换入口在管理后台；前台首页暂不提供切换（如需可扩展）。
- 用户输入数据（站点名称、描述等）不做翻译。
- 不同语言下文本长度不同，注意布局适配。

#### 扩展语言（示例）

如需添加更多语言（如日语）：

1. 创建新的语言文件：`frontend/src/locales/ja.js`
2. 在 `frontend/src/locales/index.js` 中导入并注册
3. 在语言切换器中增加入口

#### 测试建议

1. 切换语言后检查各页面文本是否正确显示。
2. 刷新页面后语言选择是否保持。
3. 不同语言下的布局是否正常。

### 数据库迁移规范（可选）

> 当前仓库尚未集成 Alembic，本节仅提供建议流程。

#### 目标

- 保证数据库结构演进可追踪、可回滚、可复现。
- 避免手工改库导致环境不一致。

#### 工具与目录（建议）

- ORM：SQLAlchemy
- 迁移工具：Alembic（建议）
- 目录建议：
  - `backend/alembic.ini`
  - `backend/alembic/env.py`
  - `backend/alembic/versions/*.py`

#### 迁移命名规则

- 文件名：`<timestamp>_<short_desc>.py`
- 示例：`20260216_103000_add_visit_stats_index.py`
- 描述要求：动词开头，明确变更对象。

#### 变更流程（建议）

1. 修改 `models.py`。
2. 生成迁移草稿：`alembic revision --autogenerate -m "add_xxx"`。
3. 人工审查脚本，确认字段/索引/约束正确。
4. 执行迁移：`alembic upgrade head`。
5. 回归验证后合并。

#### 回滚流程（建议）

- 回滚一步：`alembic downgrade -1`
- 回滚到版本：`alembic downgrade <revision_id>`
- 回滚前务必先做数据备份（尤其生产环境）。

#### 迁移脚本要求

- 必须包含 `upgrade()` 与 `downgrade()`。
- 禁止在迁移里写业务逻辑。
- 数据修复语句需具备幂等性。
- 涉及大表变更时应分批或离峰执行。

#### SQLite 特殊注意事项

- SQLite 对 `ALTER TABLE` 支持有限。
- 大变更策略：建新表 → 搬运数据 → 替换旧表。
- 迁移期间需评估锁影响。

#### 发布检查清单

- 本次 PR 是否包含迁移脚本。
- 脚本是否可在空库和已有数据库执行。
- 升级与回滚是否都验证通过。
- 与数据模型说明是否一致。

#### 示例迁移评审模板

```md
### Migration Review
- 变更点：
- 风险点：
- 是否涉及数据回填：
- 回滚方案：
- 验证结果：
```
