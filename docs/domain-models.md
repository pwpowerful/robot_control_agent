# 共享领域模型说明

本文档对应实施计划步骤 05，描述当前 MVP 已锁定的共享领域模型、模块间传递对象名称，以及关键字段语义。

## 1. 设计边界

- 本文档只定义共享对象模型，不定义数据库表结构
- 本文档只定义模块间交换的数据契约，不实现业务 API
- 本文档覆盖任务、语义动作计划、执行计划、执行结果、告警、审计、长期记忆最小字段集
- 当前代码实现位于 `backend/src/robot_control_backend/domain/models.py`

## 2. 核心业务对象

### 2.1 `TaskRecord`

用途：

- 表示任务服务、执行 Worker、前端任务详情共同使用的统一任务对象

最小字段语义：

- `task_id`：任务唯一标识
- `task_type`：当前 MVP 固定为 `pick_and_place`
- `raw_instruction`：原始自然语言指令
- `target_object`：目标物类型
- `target_location`：目标位置对象，包含工位、槽位、位姿和容差
- `status`：统一任务状态机状态
- `failure_reason`：用户可读失败原因
- `failure_category`：标准化失败类别
- `created_by`：创建人
- `created_at`：创建时间
- `robot_id`：当前机械臂标识
- `workstation_id`：单工位标识

Step 11 补充说明：

- 任务 API 当前直接返回 `TaskRecord` 作为任务列表项与任务详情主体对象
- 当前 `robot_id` 由活动配置项 `RCA_EXECUTION_ROBOT_CONFIG_ID` 提供
- 当前 `created_by` 使用提交任务的登录用户名

### 2.1.1 `TaskStatusHistoryEntry`

用途：

- 表示 Step 11 任务服务在每次状态变化时记录的状态历史条目
- 作为任务执行链路接口的组成部分，供任务详情页和后续审计回放使用

最小字段语义：

- `history_id`：状态历史条目唯一标识
- `task_id`：关联任务
- `from_status`：变更前状态，可为空
- `to_status`：变更后状态
- `changed_at`：变更时间
- `changed_by`：触发变更的操作者或系统身份
- `reason`：状态变化原因说明

### 2.2 `SemanticActionPlan`

用途：

- 表示 Planner Agent 的标准产物“语义动作计划”
- 只表达任务层面的语义步骤，不直接表达底层 SDK 执行原语

最小字段语义：

- `semantic_plan_id`：语义动作计划唯一标识
- `task_id`：关联任务
- `steps`：语义步骤序列
- `preconditions`：语义计划前置条件
- `planning_notes`：可选规划说明
- `generated_at`：语义计划生成时间

### 2.3 `ExecutionPlan`

用途：

- 表示 Coder Agent 的标准产物“可执行结构化计划”
- 也是 Critic Agent、执行层和任务详情页展示的主输入对象

最小字段语义：

- `plan_id`：计划唯一标识
- `task_id`：关联任务
- `semantic_plan_id`：来源语义动作计划标识
- `steps`：有序步骤序列
- `action_params`：每步动作参数集合
- `preconditions`：计划级前置条件
- `validation_result`：最近一次 Critic Agent 校验结果
- `allowed_to_run`：当前是否允许运行
- `script_version`：关联的受控脚本版本

### 2.4 `ExecutionResult`

用途：

- 表示 Robot 执行结果与视觉复检结果的统一输出对象

最小字段语义：

- `execution_id`：执行记录唯一标识
- `task_id`：关联任务
- `robot_status`：标准化机械臂执行状态
- `error_code`：底层错误码映射
- `vision_verification`：执行后视觉复检结果
- `memory_written`：是否已写入长期记忆
- `started_at`：执行开始时间
- `finished_at`：执行完成时间
- `failure_reason`：执行失败摘要

## 3. 补充共享对象

### 3.1 告警对象 `AlertRecord`

- `alert_id`：告警唯一标识
- `task_id`：关联任务，可为空
- `related_audit_event_id`：关联的主审计事件 ID，用于从告警详情回溯到触发原因
- `event_type`：告警事件类型
- `severity`：严重级别
- `trigger_module`：触发模块
- `message`：告警摘要
- `handling_status`：处理状态
- `occurred_at`：发生时间
- `emergency_stop_triggered`：是否触发急停

### 3.2 审计对象 `AuditRecord`

- `audit_event_id`：审计事件唯一标识
- `task_id`：关联任务，可为空
- `event_type`：审计事件类型
- `source_module`：来源模块
- `outcome`：事件结果
- `occurred_at`：事件时间
- `summary`：事件摘要
- `actor_id`：操作者或系统身份
- `status_from`：状态变更前值
- `status_to`：状态变更后值
- `payload`：结构化原始载荷

Step 11 补充说明：

- 新创建任务当前至少写入两类任务级审计事件：
  - `task_created`
  - `task_status_changed`
- `task_status_changed` 会与 `TaskStatusHistoryEntry` 保持一一对应的时间线关系

当前审计对象的载荷边界约定为：

- 只记录结构化输入摘要、上下文来源、Prompt/版本标识、结构化输出、Tool 调用记录和最终决策结果
- 不记录 Agent 原始推理全文，不持久化 raw chain-of-thought
- 若需要把告警和审计串联，优先通过 `AlertRecord.related_audit_event_id` 建立主关联，再通过 `task_id + 时间线` 回放上下文

兼容性说明：

- 当前代码中保留 `AuditEventRecord` 作为兼容别名，但规范名称以 `AuditRecord` 为准

### 3.3 长期记忆对象 `LongTermMemoryRecord`

- `memory_id`：长期记忆唯一标识
- `task_id`：关联任务
- `task_type`：任务类型
- `target_object`：目标物类型
- `key_grasp_parameters`：关键抓取参数
- `placement_parameters`：关键放置参数
- `script_version`：关联脚本版本
- `vision_verification`：成功复检结果
- `recorded_at`：写入时间
- `source_label`：来源标识

## 4. 模块间交换对象

### 4.1 Vision 相关

- `VisionLocateResult`
  - Planner Agent 的主要感知输入
  - 包含目标是否找到、目标位姿、检测物列表、危险物列表和抓拍时间
- `VisionVerificationResult`
  - 执行后复检结果
  - 包含是否通过、置信度、期望位姿、观测位姿、偏差和失败原因

### 4.2 Knowledge 相关

- `KnowledgeReference`
  - SDK 文档或 SOP 的检索结果元数据
- `TeachingSampleReference`
  - 示教样本的检索结果元数据
- `KnowledgeContextBundle`
  - Planner Agent 使用的统一知识上下文包

### 4.3 Planner Agent / Coder Agent / Critic Agent 相关

- `PlannerContext`
  - `TaskRecord + VisionLocateResult + KnowledgeContextBundle + safety_rule_set_id`
- `PlannerOutput`
  - 规划成功时包含 `SemanticActionPlan`
  - 规划失败时包含 `failure_reason`
- `CoderContext`
  - `TaskRecord + SemanticActionPlan`
- `ControlledScript`
  - Coder Agent 的受控脚本摘要对象
  - 包含脚本版本、模板版本、步骤绑定关系
- `CoderOutput`
  - `ExecutionPlan + ControlledScript + script_summary`
- `CriticContext`
  - `TaskRecord + ExecutionPlan + ControlledScript`
- `ValidationResult`
  - Critic Agent 统一校验结果
  - 包含是否允许运行、失败类别、失败描述、关联步骤、建议回退模块、详细发现列表

### 4.4 Robot 与记忆相关

- `RobotExecutionRequest`
  - 执行编排器向 Robot 适配层下发的执行请求
  - 只包含经过 Critic Agent 允许的受控步骤绑定
- `MemoryWriteCandidate`
  - 视觉复检通过后，长期记忆写入前的候选对象

## 5. 共享基础对象

### 5.1 `Pose3D`

- 统一三维位姿结构
- 使用 `frame_id` 区分坐标系
- 位置单位固定为毫米
- 姿态单位固定为角度

### 5.2 `TargetLocation`

- 统一目标放置位置对象
- 包含 `station_id`、`slot_id`、`pose`、`tolerance_mm`

### 5.3 `PlanStep`

- 表示受控执行计划中的单步动作
- 使用 `action_name` 表示白名单动作或模板名
- 使用 `expected_outcome` 明确本步预期结果

### 5.4 `ActionParameterSet`

- 表示单步动作的结构化参数
- `parameter_source` 用于标明参数来源模块

## 6. 枚举与标准化语义

当前共享枚举定义位于 `backend/src/robot_control_backend/domain/enums.py`，主要包括：

- `TaskType`
- `TaskStatus`
- `TaskFailureCategory`
- `ValidationFailureCategory`
- `ModuleName`
- `RobotExecutionStatus`
- `AlertSeverity`
- `AlertHandlingStatus`
- `AlertEventType`
- `AuditEventType`
- `AuditOutcome`

Step 07 在 `AuditEventType` 中补充了以下审计链路事件：

- `context_assembled`
- `tool_called`
- `agent_output_recorded`

这些枚举的目的只有一个：避免模块间出现“同一个含义，多种字符串写法”的问题。

## 7. 验证对照

本步骤当前通过以下方式验证：

- 共享模型代码已统一放入 `backend/src/robot_control_backend/domain/`
- `backend/tests/test_domain_models.py` 覆盖了任务、计划、执行结果、告警、审计、长期记忆最小字段集
- `backend/tests/test_audit_policies.py` 覆盖了审计链路阶段、告警级别/急停规则，以及 raw chain-of-thought 字段拦截
- 同一测试文件覆盖了 `SemanticActionPlan -> ExecutionPlan` 的对象衔接关系
- `backend/tests/test_task_state_machine.py` 覆盖了主流程、失败流程和非法状态转换
