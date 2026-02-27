# MyHarbor - 个人站点导航 需求文档

## 1. 项目概述

MyHarbor 是一个个人站点导航页面，用于集中管理和快速访问自己开发/部署的各类服务站点。提供简洁的前台展示页面和后台管理功能，支持站点状态检测。

## 2. 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端 | Python + FastAPI |
| 数据库 | SQLite (SQLAlchemy ORM) |
| 前端 | Vue 3 + Vite + TailwindCSS + vue-i18n |
| 部署 | Docker / Docker Compose |

**多语言支持：**
- 默认语言：中文（zh-CN）
- 支持语言：中文、英文
- 国际化方案：vue-i18n v11
- 语言切换：管理后台侧边栏提供语言切换功能
- 语言持久化：用户选择保存在浏览器 localStorage

## 3. 数据模型

### 3.1 站点 (Site)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 自动 | 主键，自增 |
| name | string | 是 | 站点名称 |
| url | string | 是 | 站点地址 |
| logo | string | 否 | 站点 logo（URL 或本地路径） |
| description | string | 否 | 站点简介 |
| tags | string | 否 | 类型标签，多个用逗号分隔 |
| is_public | boolean | 是 | 是否公开，默认 true |
| status | string | 是 | 站点状态：online / offline / unknown |
| sort_order | int | 否 | 排序权重，数值越小越靠前 |
| last_check_time | datetime | 否 | 最近一次状态检测时间 |
| created_at | datetime | 自动 | 创建时间 |
| updated_at | datetime | 自动 | 更新时间 |

> **级联删除：** 删除站点时，同步删除该站点关联的 SiteStatusLog、VisitLog 和 VisitStats 记录。

### 3.2 系统配置 (SiteConfig)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| key | string | 配置键 |
| value | text | 配置值 |

预置配置项：

| key | 说明 | 默认值 |
|-----|------|--------|
| site_title | 页面标题 | MyHarbor |
| site_description | 站点介绍文本（支持多行） | 欢迎来到 MyHarbor |
| copyright | 版权声明 | &copy; 2026 MyHarbor |
| icp_number | ICP 备案号 | （空） |
| admin_username | 管理员用户名 | admin |
| admin_password | 管理后台密码（哈希存储） | admin123（首次启动后强烈建议修改） |
| admin_route_code | 后台安全路由码 | 首次启动时随机生成 8 位字母数字串 |
| check_interval | 状态检测间隔（分钟） | 5 |

> **首次启动行为：** 系统自动建表并写入上述默认配置。启动日志中会打印后台访问地址（含安全路由码），提示用户尽快修改默认密码。

### 3.3 站点状态日志 (SiteStatusLog)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 自动 | 主键，自增 |
| site_id | int | 是 | 关联站点 ID |
| status | string | 是 | online / offline |
| response_time | int | 否 | 响应时间（毫秒） |
| checked_at | datetime | 自动 | 检测时间 |

> 用于生成 30 天运行状态图例，保留 30 天数据，超期自动清理。

### 3.4 访问记录 (VisitLog)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 自动 | 主键，自增 |
| site_id | int | 否 | 点击的站点 ID（null 表示仅访问首页） |
| ip | string | 否 | 访客 IP |
| user_agent | string | 否 | 浏览器 UA |
| visited_at | datetime | 自动 | 访问时间 |

### 3.5 访问统计聚合 (VisitStats)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 自动 | 主键，自增 |
| site_id | int | 否 | 站点 ID（null 表示首页整体） |
| date | date | 是 | 统计日期 |
| click_count | int | 是 | 当日点击次数 |

> 每日定时聚合，后台按日/月/年/总计查询。

## 4. 功能需求

### 4.1 前台展示页

**页面布局（从上到下）：**

```
┌──────────────────────────────────┐
│           站点标题                │
│         站点介绍文本              │
├──────────────────────────────────┤
│  [标签筛选栏]  全部 | 工具 | ...  │
├──────────────────────────────────┤
│  ┌──────┐ ┌──────┐ ┌──────┐     │
│  │ logo │ │ logo │ │ logo │     │
│  │ 名称 │ │ 名称 │ │ 名称 │     │
│  │ 状态 │ │ 状态 │ │ 状态 │     │
│  │ 标签 │ │ 标签 │ │ 标签 │     │
│  └──────┘ └──────┘ └──────┘     │
│  ┌──────┐ ┌──────┐              │
│  │ ...  │ │ ...  │              │
│  └──────┘ └──────┘              │
├──────────────────────────────────┤
│     版权声明  |  ICP 备案信息     │
└──────────────────────────────────┘
```

**功能点：**

- F1.1：显示系统配置中的站点标题和介绍文本
- F1.2：以卡片形式展示所有**公开**站点（is_public = true）
- F1.3：每张卡片显示：logo、名称、简介、标签、在线状态指示（绿色/红色圆点）
  - Logo 缺省处理：未设置 logo 时，取站点名称首字作为彩色字母头像
- F1.4：点击卡片跳转到对应站点（新标签页打开）
- F1.5：支持按标签筛选站点
- F1.6：支持按名称搜索站点
- F1.7：响应式布局，适配桌面端和移动端
- F1.8：页面底部显示版权声明和 ICP 备案信息
- F1.9：支持亮色/暗色模式切换，默认跟随系统偏好

### 4.2 管理后台

**访问方式：** 通过 `/<安全路由码>` 路径访问（如 `/a3x9k`），安全路由码在系统配置中设置，避免后台入口被猜到。首次启动时随机生成，可在后台修改。

**功能点：**

- F2.1：用户名 + 密码登录，登录后通过 JWT Token 维持会话
  - JWT Token 有效期 24 小时，过期后需重新登录
  - 登录接口限流：同一 IP 每分钟最多 5 次尝试，超出后锁定 15 分钟
  - 安全路由码修改后，后端返回新路由码，前端自动跳转到新路径
- F2.2：站点列表（展示全部站点，包括非公开的）
  - 支持按标签、状态、公开/隐藏筛选
  - 支持拖拽或手动输入排序权重调整站点顺序
- F2.3：添加站点
  - 表单字段：名称、URL、logo、简介、标签、是否公开、排序权重
  - URL 格式校验
  - logo 支持输入 URL 地址
- F2.4：编辑站点
  - 可修改所有字段
- F2.5：删除站点
  - 需二次确认
- F2.6：切换站点公开状态
  - 快捷开关，无需进入编辑页
- F2.7：手动检测单个站点状态
- F2.8：批量检测所有站点状态
- F2.9：查看单个站点最近 30 天运行状态图例（类似 UptimeRobot 风格的横向色块图）
- F2.10：系统设置
  - 修改站点标题、介绍文本、版权声明、备案号
  - 修改管理员用户名和密码
  - 修改后台安全路由码
  - 修改状态检测间隔时间
- F2.11：访问统计面板
  - 首页总到访次数（日/月/年/总计）
  - 各站点点击次数（日/月/年/总计）
  - 简单的趋势图表
- F2.12：数据备份与恢复
  - 导出：将所有站点数据导出为 JSON 文件下载
  - 导入：上传 JSON 文件批量导入站点（重复 URL 跳过或覆盖，由用户选择）

### 4.3 凭证恢复

- F3.1：提供 CLI 管理脚本 `python manage.py`，支持以下命令：
  - `python manage.py reset-admin` — 重置管理员用户名和密码为默认值
  - `python manage.py show-admin` — 查看当前管理员用户名
  - `python manage.py show-route` — 查看当前后台安全路由码
  - `python manage.py set-admin --username <name> --password <pass>` — 直接设置管理员凭证

### 4.4 站点状态检测

- F4.1：对站点 URL 发起 HTTP 请求，根据响应状态码判断在线/离线
  - 2xx/3xx/4xx（< 500）→ online（服务器在线）
  - 5xx（>= 500）→ offline（服务器错误）
  - 异常/超时 → offline（无法连接）
  - 未检测 → unknown
  - 说明：4xx 状态码（如 403）表示服务器在线但拒绝访问，常见于防护机制
- F4.2：后台定时检测，间隔时间可在管理后台配置（默认 5 分钟）
- F4.3：每次检测结果写入 SiteStatusLog 表，记录状态和响应时间
- F4.4：管理后台支持手动触发单个/全部检测
- F4.5：保留最近 30 天检测记录，超期数据自动清理（每日清理一次）
- F4.6：30 天运行状态图例
  - 横向色块展示，每个色块代表一段时间的状态
  - 绿色 = online，红色 = offline，灰色 = 无数据
  - 鼠标悬停显示具体时间和响应时间

### 4.5 访问统计

- F5.1：前台首页被访问时记录一条 VisitLog（site_id 为空）
- F5.2：用户点击站点卡片时记录一条 VisitLog（携带 site_id），然后跳转
- F5.3：每日凌晨定时聚合前一天的 VisitLog 到 VisitStats 表
- F5.4：管理后台统计面板展示：
  - 首页总访问量（日/月/年/总计）
  - 各站点点击量排行（日/月/年/总计）
  - 可选：简单折线图展示近 30 天趋势
- F5.5：VisitLog 原始数据保留 90 天，超期自动清理

## 5. API 设计

### 5.1 公开接口（无需认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| GET | /api/sites/public | 获取所有公开站点列表 |
| GET | /api/config/public | 获取公开配置（标题、介绍、版权、备案） |
| POST | /api/visit | 记录首页访问 |
| POST | /api/visit/{site_id} | 记录站点点击 |

### 5.2 管理接口（需 JWT 认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 管理员登录（用户名 + 密码） |
| GET | /api/auth/me | 获取当前登录用户信息 |
| GET | /api/sites | 获取全部站点（含非公开） |
| POST | /api/sites | 添加站点 |
| PUT | /api/sites/{site_id} | 更新站点 |
| DELETE | /api/sites/{site_id} | 删除站点（级联删除关联日志） |
| PATCH | /api/sites/{site_id}/toggle | 切换站点公开状态 |
| PUT | /api/sites/sort | 批量更新站点排序 |
| POST | /api/sites/{site_id}/check | 检测单个站点状态 |
| POST | /api/sites/check-all | 检测所有站点状态 |
| GET | /api/sites/{site_id}/status-logs | 获取站点 30 天状态日志 |
| GET | /api/stats/overview | 访问统计概览（日/月/年/总计） |
| GET | /api/stats/sites | 各站点点击排行 |
| GET | /api/stats/trend | 近 30 天访问趋势 |
| GET | /api/config | 获取所有系统配置 |
| PUT | /api/config | 更新系统配置 |
| GET | /api/backup/export | 导出所有站点数据为 JSON |
| POST | /api/backup/import | 导入站点数据（JSON 上传） |

## 6. 非功能需求

- NF1：SQLite 单文件数据库，数据文件存放在可挂载的目录中，方便 Docker 持久化
- NF2：首次启动自动初始化数据库表和默认配置
- NF3：前端打包后由 FastAPI 静态托管，单服务部署
- NF4：提供 Dockerfile 和 docker-compose.yml
- NF5：支持通过环境变量覆盖默认配置（端口、数据库路径等）
- NF6：状态检测请求超时时间 5 秒，避免阻塞
- NF7：提供 manage.py CLI 脚本用于凭证恢复和基本运维
- NF8：SiteStatusLog 保留 30 天，VisitLog 保留 90 天，定时自动清理

## 7. 项目结构（规划）

```
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
│   │   │   ├── public.py        # 公开接口（站点列表、配置、访问记录）
│   │   │   └── health.py        # 健康检查接口
│   │   ├── services/
│   │   │   ├── site_checker.py  # 站点状态检测
│   │   │   ├── stats_service.py # 统计聚合服务
│   │   │   ├── scheduler.py     # 定时任务（检测 + 聚合 + 清理）
│   │   │   └── bootstrap.py     # 启动初始化服务
│   │   └── utils/
│   │       ├── security.py      # 密码哈希、JWT 工具
│   │       └── rate_limiter.py  # 登录限流
│   ├── tests/                   # 测试文件
│   ├── manage.py                # CLI 管理脚本（凭证重置/查询）
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
│   │   │   ├── client.js        # Axios 客户端 + 拦截器
│   │   │   ├── auth.js          # 认证相关 API
│   │   │   ├── sites.js         # 站点相关 API
│   │   │   ├── stats.js         # 统计相关 API
│   │   │   ├── config.js        # 配置相关 API
│   │   │   └── public.js        # 公开 API
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
├── docs/
│   ├── PRD.md                   # 产品需求文档
│   ├── TECH.md                  # 技术设计文档
│   ├── API_CONTRACT.md          # API 契约文档
│   ├── CODING_RULES.md          # 开发规范
│   ├── ENV.md                   # 环境变量说明
│   ├── I18N.md                  # 多语言使用文档
│   ├── DB_MIGRATIONS.md         # 数据库迁移文档
│   ├── TEST_CASES.md            # 测试用例文档
│   ├── TASKS.md                 # 任务拆解清单
│   ├── ROADMAP.md               # 开发路线图
│   └── RUNBOOK.md               # 运维手册
└── README.md
```
