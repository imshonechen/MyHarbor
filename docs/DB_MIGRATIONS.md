# MyHarbor 数据库迁移规范

## 1. 目标

- 保证数据库结构演进可追踪、可回滚、可复现。
- 避免手工改库导致环境不一致。

## 2. 工具与目录

- ORM：SQLAlchemy
- 迁移工具：Alembic（建议）
- 目录建议：
  - `backend/alembic.ini`
  - `backend/alembic/env.py`
  - `backend/alembic/versions/*.py`

## 3. 迁移命名规则

- 文件名：`<timestamp>_<short_desc>.py`
- 示例：`20260216_103000_add_visit_stats_index.py`
- 描述要求：动词开头，明确变更对象。

## 4. 变更流程

1. 修改 `models.py`。
2. 生成迁移草稿：`alembic revision --autogenerate -m "add_xxx"`。
3. 人工审查脚本，确认：
   - 字段类型正确
   - 索引/唯一约束正确
   - 外键级联行为正确
4. 执行迁移：`alembic upgrade head`。
5. 回归验证后合并。

## 5. 回滚流程

- 回滚一步：`alembic downgrade -1`
- 回滚到版本：`alembic downgrade <revision_id>`
- 回滚前务必先做数据备份（尤其生产环境）。

## 6. 迁移脚本要求

- 必须包含 `upgrade()` 与 `downgrade()`。
- 禁止在迁移里写业务逻辑。
- 数据修复语句需具备幂等性。
- 涉及大表变更时应分批或离峰执行。

## 7. SQLite 特殊注意事项

- SQLite 对 `ALTER TABLE` 支持有限。
- 大变更策略：
  - 建新表
  - 搬运数据
  - 替换旧表
- 迁移期间需评估锁影响。

## 8. 发布检查清单

- 本次 PR 是否包含迁移脚本。
- 脚本是否可在空库和已有数据库执行。
- 升级与回滚是否都验证通过。
- 与 `docs/TECH.md` 的数据模型说明是否一致。

## 9. 示例迁移评审模板

```md
### Migration Review
- 变更点：
- 风险点：
- 是否涉及数据回填：
- 回滚方案：
- 验证结果：
```
