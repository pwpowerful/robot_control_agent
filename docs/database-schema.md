# 数据库结构设计说明

本文档对应实施计划步骤 06，描述当前 MVP 已落地的 PostgreSQL 16 数据库基线、约束设计和向量字段设计。

## 1. 设计边界

- 当前数据库实现仅覆盖 ORM 元数据、Alembic 迁移脚手架和首个迁移版本。
- 当前不实现数据库会话工厂、Repository、Service 持久化逻辑或 Worker 任务队列消费逻辑。
- 当前数据库模型服务于单工位、单机器人、单机部署的 MVP 边界。
- 审计层只持久化结构化输入摘要、上下文来源、结构化输出、Tool 调用记录和最终决策，不持久化 raw chain-of-thought。

## 2. 表分组

### 2.1 身份与会话

- `users`：系统用户主表，支持软删除和激活状态。
- `roles`：角色定义表，支持软删除和激活状态。
- `user_roles`：用户与角色多对多关系表。
- `sessions`：服务端会话表，存储会话令牌哈希、过期时间和撤销时间。

### 2.2 任务与执行链路

- `tasks`：任务主表，保存原始指令、目标物、目标位置、任务状态、失败类别、机器人标识和工位标识。
- `semantic_action_plans`：Planner Agent 输出的语义动作计划。
- `execution_plans`：Coder Agent 输出的可执行结构化计划，并挂接脚本工件引用和最近一次校验结果。
- `execution_results`：Robot 执行结果与视觉复检结果摘要。

### 2.3 审计与告警

- `alerts`：标准化告警记录，支持事件类型、严重级别、处理状态、触发模块检索，并通过 `related_audit_event_id` 关联主审计事件。
- `audit_records`：全链路审计记录，支持任务、模块、状态流转和时间检索。

### 2.4 知识、示教与长期记忆

- `knowledge_items`：SDK 文档、SOP 等知识条目。
- `teaching_samples`：人工示教样本。
- `long_term_memories`：仅保存视觉复检成功后的长期记忆经验。

### 2.5 配置与工件引用

- `artifact_references`：本地文件系统等外部工件的统一引用表。
- `robot_configs`：机器人配置。
- `safety_rule_sets`：安全规则配置。
- `system_configs`：系统级配置键值表。

## 3. 主键、外键与约束策略

- 所有主业务表均使用字符串主键，便于和任务链路、工件引用、审计记录做跨模块关联。
- `users.username`、`roles.role_code`、`sessions.session_token_hash`、`robot_configs.robot_id`、`safety_rule_sets.rule_set_name`、`system_configs(config_namespace, config_key)` 使用唯一约束防止重复配置。
- `user_roles` 使用组合主键 `(user_id, role_id)`，防止重复授权。
- 核心任务链使用显式外键：
  - `semantic_action_plans.task_id -> tasks.task_id`
  - `execution_plans.task_id -> tasks.task_id`
  - `execution_plans.semantic_plan_id -> semantic_action_plans.semantic_plan_id`
  - `execution_results.task_id -> tasks.task_id`
  - `execution_results.plan_id -> execution_plans.plan_id`
- 审计与告警对任务使用可空外键，允许记录全局系统事件。
- `alerts.related_audit_event_id -> audit_records.audit_event_id` 用于将告警详情回溯到触发它的主审计事件。
- 工件引用通过 `artifact_references` 统一关联知识条目、示教样本、执行脚本和执行结果附件。

## 4. 审计字段与删除策略

- 可变配置与知识类表使用 `created_at`、`updated_at`、`deleted_at` 三元组，支持软删除与后续变更追踪。
- 任务、计划、执行结果、告警、审计记录和长期记忆采用追加写或不可变写法，不提供软删除字段。
- 会话表使用 `revoked_at` 而不是删除记录，以支持审计追踪。

## 5. 索引策略

当前已落实的关键索引包括：

- 任务检索：
  - `tasks(status, created_at)`
  - `tasks(robot_id, created_at)`
  - `tasks(workstation_id, created_at)`
- 告警检索：
  - `alerts(task_id, occurred_at)`
  - `alerts(handling_status, occurred_at)`
  - `alerts(severity, occurred_at)`
  - `alerts(related_audit_event_id)`
- 审计检索：
  - `audit_records(task_id, occurred_at)`
  - `audit_records(source_module, occurred_at)`
  - `audit_records(status_to, occurred_at)`
- 元数据过滤：
  - `knowledge_items.retrieval_metadata` GIN 索引
  - `teaching_samples.retrieval_metadata` GIN 索引
  - `long_term_memories.retrieval_metadata` GIN 索引
- 长期记忆过滤：
  - `long_term_memories(workstation_id, task_type, target_object)`
  - `long_term_memories(robot_id, recorded_at)`

## 6. pgvector 字段设计

- `knowledge_items.embedding`
- `teaching_samples.embedding`
- `long_term_memories.embedding`

三类向量字段当前统一使用 `vector(1536)`，作为共享模型嵌入维度的保守默认值。

每类向量表同时保留 `retrieval_metadata` JSONB 字段，用于先做元数据过滤，再做向量近邻搜索，符合设计文档对 Memory Layer 的检索要求。

当前首个迁移已创建 HNSW 索引：

- `ix_knowledge_items_embedding_hnsw`
- `ix_teaching_samples_embedding_hnsw`
- `ix_long_term_memories_embedding_hnsw`

## 7. 当前未覆盖内容

- 数据库连接池与会话管理
- PostgreSQL 行锁任务队列实现
- 审计写入服务
- 告警聚合和处理流
- 知识库导入与向量化流水线
- 长期记忆写入策略执行逻辑
