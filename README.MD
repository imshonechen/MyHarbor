# MyHarbor - 个人站点导航

一个简洁优雅的个人站点导航页面，用于集中管理和快速访问自己开发/部署的各类服务站点。

## ✨ 特性

- 🎨 **简洁美观** - 现代化的 UI 设计，支持亮暗模式
- 🌐 **多语言支持** - 默认中文，支持中英文切换
- 📊 **站点监控** - 自动检测站点状态，30 天运行状态图例
- 📈 **访问统计** - 记录访问数据，提供统计分析
- 🔐 **安全管理** - JWT 认证，动态后台路由，登录限流
- 🏷️ **标签分类** - 支持标签筛选和搜索
- 📱 **响应式设计** - 完美适配桌面端和移动端
- 🐳 **容器化部署** - 提供 Docker 一键部署方案

## 🌍 多语言支持

MyHarbor 支持多语言界面，默认语言为**中文**：

- ✅ 中文（简体）- 默认
- ✅ English
- 🎯 语言切换：登录管理后台后，在侧边栏底部可切换语言
- 💾 语言持久化：用户选择的语言会自动保存

详细说明请查看：[技术文档（多语言 i18n）](docs/TECH.md#多语言i18n)

## 🚀 技术栈

**后端：**
- Python 3.10+
- FastAPI
- SQLAlchemy + SQLite
- APScheduler

**前端：**
- Vue 3 (Composition API)
- Vite
- TailwindCSS
- vue-i18n (国际化)

## 📦 快速开始

### 使用 Docker Compose（推荐）

```bash
# 启动服务
docker compose up -d

# 访问应用
# 前台：http://localhost:24041
# 后台：http://localhost:24041/{安全路由码}
```

> 如果你的环境还在使用旧版 Docker Compose，可将 `docker compose` 替换为 `docker-compose`。

### 本地开发

**后端：**

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 24041
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

## 📖 文档

- [文档导航（推荐先读）](docs/README.md)
- [产品需求文档（含路线图/任务/测试用例）](docs/PRD.md)
- [技术设计文档（含环境变量/开发规范/i18n/迁移规范）](docs/TECH.md)
- [API 契约文档](docs/API_CONTRACT.md)
- [生产部署指南](DEPLOYMENT.md)

## 🎯 功能概览

### 前台展示页

- 展示所有公开站点
- 标签筛选和搜索
- 站点状态实时显示
- 响应式卡片布局

### 管理后台

- **仪表盘** - 数据概览和快捷操作
- **站点管理** - CRUD 操作、排序、状态检测
- **访问统计** - 访问量统计和趋势分析
- **站点监控** - 30 天运行状态图例
- **系统设置** - 站点配置、账号管理、监控设置
- **数据备份** - 导出/导入站点数据
- **语言切换** - 中英文界面切换

## 🔧 配置说明

### 环境变量

```bash
# 应用端口
APP_PORT=24041

# 数据库路径
DATABASE_URL=sqlite:///./data/myharbor.db

# JWT 密钥
JWT_SECRET=your-secret-key

# JWT 过期时间（小时）
JWT_EXPIRE_HOURS=24

# 站点检测超时（秒）
CHECK_TIMEOUT_SECONDS=5

# 日志级别
LOG_LEVEL=INFO
```

更多环境变量说明请查看：[技术文档（环境变量）](docs/TECH.md#环境变量)。

> 站点检测“间隔（分钟）”属于系统配置 `check_interval`（默认 5），可在管理后台「系统设置」里修改。

### 首次启动

首次启动时，系统会自动：
1. 创建数据库表
2. 生成默认配置
3. 创建管理员账号（默认：admin/admin123）
4. 生成随机的后台安全路由码

**重要：** 首次登录后请立即修改默认密码！

## 🛠️ CLI 管理工具

```bash
# 重置管理员账号
python backend/manage.py reset-admin

# 查看管理员用户名
python backend/manage.py show-admin

# 查看后台路由码
python backend/manage.py show-route

# 设置管理员账号
python backend/manage.py set-admin --username admin --password newpass
```


## 📝 开发计划

- [x] 基础框架搭建
- [x] 站点管理功能
- [x] 状态检测功能
- [x] 访问统计功能
- [x] 多语言支持
- [ ] 数据可视化增强
- [ ] 更多主题支持
