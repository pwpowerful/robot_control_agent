# 任务状态机说明

本文档对应实施计划步骤 05，描述当前 MVP 的统一任务状态机。

## 1. 设计目标

统一状态机要解决三个问题：

1. 任务生命周期必须只有一套状态定义
2. 所有模块都必须共享同一套状态转移规则
3. 主流程、失败流程和急停流程都必须可审计、可解释、无歧义

当前代码实现位于 `backend/src/robot_control_backend/domain/state_machine.py`。

## 2. 状态清单

当前统一状态只有以下 9 个：

- `created`
- `planning`
- `validating`
- `ready_to_run`
- `running`
- `verifying`
- `succeeded`
- `failed`
- `emergency_stopped`

其中终态只有：

- `succeeded`
- `failed`
- `emergency_stopped`

## 3. 主流程

标准成功链路如下：

`created -> planning -> validating -> ready_to_run -> running -> verifying -> succeeded`

说明：

- 该状态机是**任务级粗粒度状态机**，不与 Agent 角色一一对应
- `planning` 阶段覆盖 Planner 生成语义动作计划，以及 Coder 将其物化为可执行结构化计划与受控脚本摘要
- `validating` 阶段专门对应 Critic 对执行级产物的规则校验与轨迹检查

语义说明：

- `created`：任务已持久化，等待进入执行链路
- `planning`：正在生成语义动作计划，并将其物化为执行级计划工件
- `validating`：正在由 Critic Agent 对执行级计划与受控脚本摘要进行规则校验与轨迹检查
- `ready_to_run`：已通过校验，等待进入唯一执行槽位
- `running`：Robot 正在执行
- `verifying`：执行后视觉复检中
- `succeeded`：复检通过，任务完成，可进入长期记忆写入链路

## 4. 失败与回退流程

### 4.1 规划失败

- `planning -> failed`

触发条件：

- 目标无法定位
- 输入关键信息缺失
- 任务不在 MVP 支持范围内
- 内部最大尝试次数耗尽

### 4.2 校验失败并回退

- `validating -> planning`

触发条件：

- Critic Agent 发现可修复问题
- 当前仍有剩余内部尝试次数

### 4.3 校验终止失败

- `validating -> failed`

触发条件：

- Critic Agent 发现终止性问题
- 或内部重试次数已经用尽

### 4.4 执行失败

- `running -> failed`

触发条件：

- 机械臂返回 `Execution_Interrupted`
- 夹爪滑落
- 目标丢失
- 工作空间违规
- 碰撞或等价执行失败

### 4.5 复检失败

- `verifying -> failed`

触发条件：

- 视觉复检置信度低于阈值
- 放置偏差超过容差
- 最终目标未达到预期位置

## 5. 急停流程

任何安全停机事件都不再进入普通失败态，而是直接进入：

- `planning -> emergency_stopped`
- `validating -> emergency_stopped`
- `ready_to_run -> emergency_stopped`
- `running -> emergency_stopped`
- `verifying -> emergency_stopped`

设计原因：

- `failed` 表示普通终止失败
- `emergency_stopped` 表示安全优先级最高的终止态
- 两者语义必须严格区分，避免前端、审计、告警误读

## 6. 各状态规则

### 6.1 `created`

允许进入条件：

- 任务基础字段完整
- API 层已接受任务结构

允许退出条件：

- Worker 成功领取任务
- 激活配置与安全上下文可加载

失败转移条件：

- 若任务在持久化前即被拒绝，则不应进入本状态

### 6.2 `planning`

允许进入条件：

- 任务来自 `created`
- 或来自 `validating` 的回退重试

允许退出条件：

- 已生成语义动作计划，并已物化为可执行结构化计划，可进入 `validating`
- 或已产生终止性失败结论

失败转移条件：

- 普通失败：目标缺失、输入缺失、超出范围、重试耗尽
- 急停失败：危险目标进入工作区

### 6.3 `validating`

允许进入条件：

- 语义动作计划存在
- 可执行结构化计划存在
- 受控脚本摘要存在

允许退出条件：

- 校验通过进入 `ready_to_run`
- 校验失败回退 `planning`
- 校验终止失败进入 `failed`

失败转移条件：

- 可修复问题且仍可重试：`planning`
- 不可修复问题或重试耗尽：`failed`
- 安全停机：`emergency_stopped`

### 6.4 `ready_to_run`

允许进入条件：

- `allowed_to_run = true`
- 已获得单工位唯一执行权

允许退出条件：

- 已向 Robot 适配层成功下发执行请求

失败转移条件：

- 执行前条件失效：`failed`
- 执行前急停：`emergency_stopped`

### 6.5 `running`

允许进入条件：

- 受控脚本已下发
- Robot 已开始执行

允许退出条件：

- Robot 返回结构化执行结果

失败转移条件：

- 普通执行失败：`failed`
- 安全停机：`emergency_stopped`

### 6.6 `verifying`

允许进入条件：

- 执行阶段未发生终止性错误
- 已发起视觉复检

允许退出条件：

- 复检成功进入 `succeeded`
- 复检失败进入 `failed`

失败转移条件：

- 复检未达标：`failed`
- 复检阶段安全停机：`emergency_stopped`

### 6.7 `succeeded`

允许进入条件：

- 视觉复检通过阈值和容差要求

允许退出条件：

- 无

失败转移条件：

- 无

### 6.8 `failed`

允许进入条件：

- 产生标准化失败类别和可读失败原因

允许退出条件：

- 无

失败转移条件：

- 无

### 6.9 `emergency_stopped`

允许进入条件：

- 危险目标、急停命令或等价安全停机事件被触发

允许退出条件：

- 无

失败转移条件：

- 无

## 7. 无歧义性约束

当前状态机明确避免以下问题：

- 不存在“已校验但未准备执行”这种模糊状态，统一使用 `ready_to_run`
- 不存在“失败但同时急停”的双重终态，急停一律进入 `emergency_stopped`
- 不存在“校验失败后仍停留 validating”的含糊回写，必须明确去 `planning`、`failed` 或 `emergency_stopped`

## 8. 当前验证方式

- `backend/tests/test_task_state_machine.py` 覆盖主流程转移
- 同一测试文件覆盖 `validating -> planning` 的回退重试
- 同一测试文件覆盖 `planning/running/verifying` 的失败和急停流转
- 同一测试文件覆盖非法跳转拦截
