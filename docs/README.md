# 文档导航（先读这个）

> 目标：让文档“少走弯路、以一个真源为准”。如果你只想快速跑起来，请直接看根目录 `README.MD`。

## 快速索引（按角色）

### 我是使用者 / 运维

- 生产部署：`DEPLOYMENT.md`
- 日常运维/故障排查：`docs/RUNBOOK.md`
- 1Panel 部署：`docs/1PANEL_DEPLOYMENT.md`

### 我是前后端开发

- 技术设计（架构/模块/数据库/实现细节；附录含环境变量/开发规范/i18n/迁移规范）：`docs/TECH.md`
- API 契约（联调基线）：`docs/API_CONTRACT.md`

### 我是产品/项目管理

- 产品需求（含路线图/任务拆解/测试用例）：`docs/PRD.md`

## “以谁为准”（避免重复导致的冲突）

- **API 联调口径**：以 `docs/API_CONTRACT.md` 为准。
- **环境变量**：以 `backend/app/config.py` 的 `Settings` 字段为准；文档汇总在 `docs/TECH.md` 的「环境变量」小节。
- **站点检测判定**：以 `backend/app/services/site_checker.py` 为准；需求与测试用例应与其一致。

## 文档维护建议（两次 PR 策略）

- PR1（小而稳）：补齐导航、修正与代码不一致/过期内容，让文档“可信”。
- PR2（结构优化）：删除已合并的旧文档文件，更新入口链接，减少文件数量与重复段落。
