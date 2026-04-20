# 审计与告警写入规则

本文对应实施计划 Step 07，定义当前 MVP 对“哪些事件必须写审计、哪些事件需要触发告警或急停”的统一规则。

## 1. 设计边界

- 本文只定义写入规则和结构化约束，不实现 API、Repository 或后台写入服务
- 本文约束的代码落点位于 `backend/src/robot_control_backend/audit/policies.py`
- 当前规则服务于单工位、单机器人、无真实硬件接入的 MVP 边界
- 当前规则优先保证安全、审计完整性和可回放性，而不是兼顾未来的通用性

## 2. 必写审计事件

以下阶段必须具备对应的审计落点：

1. 指令接收
2. 上下文装配
3. Tool 调用
4. Agent 输出
5. 校验决策
6. 执行结果
7. 视觉复检
8. 长期记忆写入
9. 告警创建

当前代码中使用 `AuditTrailStage` 对这些阶段做统一归类，并通过 `AUDIT_EVENT_RULES` 将具体 `AuditEventType` 映射到阶段。

## 3. 当前事件映射

当前已落地的关键映射包括：

- `task_created -> instruction`
- `context_assembled -> context_assembly`
- `knowledge_retrieved -> context_assembly`
- `tool_called -> tool_call`
- `vision_located -> tool_call`
- `agent_output_recorded -> agent_output`
- `plan_generated -> agent_output`
- `script_generated -> agent_output`
- `validation_completed -> validation`
- `robot_executed -> execution`
- `vision_verified -> verification`
- `memory_written -> memory_write`
- `alert_created -> alert`

## 4. 告警默认级别与急停策略

当前 `ALERT_WRITE_RULES` 固化了以下默认规则：

- `dangerous_object_detected`：`critical`，必须触发急停
- `validation_failed`：`high`，阻断执行，但默认不触发机器人急停
- `execution_failed`：`critical`，必须触发急停
- `verification_failed`：`high`，必须触发急停并阻止后续自动动作
- `emergency_stopped`：`critical`，天然属于急停事件

## 5. 审计到告警的升级规则

当前 `ALERT_ESCALATION_RULES` 约定了下列升级路径：

- `vision_located + emergency -> dangerous_object_detected`
- `validation_completed + failed -> validation_failed`
- `robot_executed + failed/emergency -> execution_failed`
- `vision_verified + failed -> verification_failed`
- `task_status_changed + emergency -> emergency_stopped`

这些规则的目的不是替代后续服务层实现，而是提前锁定“什么情况一定要报警”和“什么情况必须停机”的统一口径。

## 6. 审计载荷禁止项

审计层只允许保存以下内容：

- 结构化输入摘要
- 上下文来源
- Prompt 或版本标识
- 结构化输出摘要
- Tool 请求/返回摘要
- 最终决策结果

审计层明确禁止写入：

- raw chain-of-thought
- reasoning trace
- scratchpad
- internal reasoning
- 其他等价的原始推理字段

当前代码通过以下能力执行该约束：

- `FORBIDDEN_AUDIT_PAYLOAD_KEYS`
- `find_forbidden_audit_payload_paths(...)`
- `assert_audit_payload_is_safe(...)`

## 7. 告警与审计关联规则

- 每条告警都可以通过 `related_audit_event_id` 指向一个主审计事件
- 该主审计事件用于解释“为什么会产生这条告警”
- 若需要回放更完整链路，应再结合 `task_id` 和时间线查询其余审计记录
- 该设计优先保证最小实现、可查询和可追溯，不在 Step 07 引入额外关联表

## 8. 当前验证方式

- `backend/tests/test_audit_policies.py` 验证审计阶段覆盖
- `backend/tests/test_audit_policies.py` 验证告警级别和急停策略
- `backend/tests/test_audit_policies.py` 验证 raw chain-of-thought 字段拦截
- `backend/tests/test_database_schema.py` 验证 `alerts.related_audit_event_id` 的 schema 和迁移
