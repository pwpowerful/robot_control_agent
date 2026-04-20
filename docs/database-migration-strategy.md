# 数据库迁移策略说明

本文档对应实施计划步骤 06，描述当前数据库迁移基线和后续演进规则。

## 1. 当前迁移基线

- 迁移工具：`Alembic`
- ORM 元数据来源：`backend/src/robot_control_backend/database/`
- 首个迁移版本：`20260416_01`
- 当前迁移目标：一次性建立 Step 06 所需的核心表、枚举、JSONB 字段、`pgvector` 扩展和向量索引

## 2. 环境与配置约定

- Alembic 通过 `backend/alembic.ini` 和 `backend/alembic/env.py` 运行。
- 数据库地址从以下顺序解析：
  1. 进程环境变量 `RCA_DATABASE_URL`
  2. `.env.<RCA_APP_ENV>`
  3. `.env`
- 若未提供 `RCA_DATABASE_URL`，迁移命令直接失败，避免在未知环境下执行。

推荐命令：

```powershell
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head --sql
```

## 3. 版本控制策略

- 采用单线性迁移历史，不在当前 MVP 阶段引入多分支迁移。
- 已发布或已被应用的迁移文件不做就地重写；结构变更通过新增 revision 表达。
- 数据库枚举、约束、索引和扩展变更必须通过 Alembic revision 显式落地。
- 任何跨表字段重命名、约束收紧或数据回填，都应拆分为“扩展 -> 回填 -> 收口”三个可回滚步骤，避免一次性破坏运行环境。

## 4. pgvector 与索引策略

- 初始迁移使用 `CREATE EXTENSION IF NOT EXISTS vector`，确保空数据库可直接初始化。
- 由于当前项目只需要 PostgreSQL 原生能力，向量字段直接放在主库中，不引入独立向量数据库。
- 向量索引当前使用 HNSW，为知识条目、示教样本和长期记忆预留后续相似检索能力。
- 元数据过滤字段使用 JSONB + GIN 组合，为先过滤再向量检索的流程打底。

## 5. 后续迁移实施规则

- 每次 revision 只解决一个清晰的结构变化主题，例如“新增审计写入字段”或“补充任务队列表索引”。
- 新增非空字段时优先先允许为空或提供服务端默认值，待数据回填后再收紧约束。
- 删除字段或删除枚举值前，先确认相关后端逻辑、前端展示和审计查询均已迁移。
- 任何涉及任务状态、告警状态、审计检索字段和长期记忆检索键的变更，都必须补自动化测试。

## 6. 当前验证方式

步骤 06 当前采用以下验证方式：

- `backend/tests/test_database_schema.py` 验证核心表、外键、唯一约束、关键索引和向量字段是否已在 ORM 元数据中声明。
- 使用 `uv run alembic upgrade head --sql` 验证迁移脚手架可生成 PostgreSQL SQL，而不依赖真实数据库连接。
- 真实 PostgreSQL 空库迁移验证留待后续联调环境执行。
