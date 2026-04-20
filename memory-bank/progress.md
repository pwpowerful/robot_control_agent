# 里程碑与当前实现状态

## 1. 当前阶段

当前项目处于：**后端业务接口继续落地阶段（步骤 03、步骤 04、步骤 05、步骤 06、步骤 07、步骤 08、步骤 09、步骤 10、步骤 11 已完成并通过验收，下一步进入步骤 12：知识库、示教样本与长期记忆管理接口）**

当前阶段边界：

- 已完成后端工程基础初始化，并通过本地验证
- 已完成前端工程基础初始化，并通过本地验证
- 已完成共享领域模型与任务状态机，并与最新实施计划对齐
- 已完成数据库模型、Alembic 脚手架与初始迁移基线
- 已完成审计与告警数据模型、写入规则和增量迁移基线
- 当前已经完成 Step 07 的本地验证与用户验收
- 当前已经完成 Step 08 的本地验证与用户验收
- 当前已经完成 Step 09 的代码实现、本地验证与用户验收
- 当前已经完成 Step 10 的代码实现、本地验证与用户验收
- 当前下一里程碑为步骤 12：知识库、示教样本与长期记忆管理接口
- 当前尚未进入 Worker 闭环，但已开始进入首批真实业务接口实现

## 2. 已完成事项

- 完成产品设计文档 `design_document.md`
- 完成技术栈文档 `tech_stack.md`
- 完成实施计划文档 `implementation_plan.md`
- 完成工作区约束文档 `AGENTS.md`
- 补齐并更新当前系统架构真相文档 `architecture.md`
- 锁定关键实施澄清项：
  - Windows 宿主机
  - 机械臂与视觉均使用模拟适配器
  - 当前实现默认跳过真实设备联调
  - 使用 API 调用共享模型
  - 单工位同一时刻仅一个任务执行
  - 管理员录入安全规则
  - 危险目标触发全局停机
  - 内部最大尝试次数 3
  - 放置位置容差 5 mm
  - 视觉复检阈值 0.7
  - 单次任务最大允许时长 60 s
- 仓库已具备基础目录骨架：`backend/`、`frontend/`、`docs/`、`infrastructure/`、`tests/`
- 完成步骤 03：初始化后端工程基础
- 后端已固定 `Python 3.11 + uv` 工程约定，并提交锁文件 `uv.lock`
- 后端已建立最小 FastAPI 启动入口、配置入口与日志入口
- 后端已明确开发、测试、生产环境配置隔离方式
- 后端已补充配置校验命令、启动命令、示例环境文件和 smoke tests
- 步骤 03 验证已通过：
  - `uv sync --group dev`
  - `uv run pytest`
  - `uv run robot-control-config-check`
  - 最小应用启动后可返回 `/openapi.json`
  - 生产环境缺失关键配置时会直接报出清晰错误
- 完成步骤 04：初始化前端工程基础
- 前端已固定 `Node.js + React 19 + TypeScript + Vite 8 + Ant Design` 工程约定，并生成 `package-lock.json`
- 前端已建立应用壳、基础路由框架、页面目录、通用组件目录、API 目录和状态管理目录边界
- 前端已统一路由命名规则、页面命名规则和状态管理命名规则
- 前端已补充环境变量示例和目录约定说明
- 步骤 04 验证已通过：
  - `npm.cmd install`
  - `npm.cmd run build`
  - `npm.cmd run dev`
  - `/` 路由返回 `200`
  - `/tasks/new` 路由返回 `200`
- 完成步骤 05：共享领域模型与任务状态机定义更新
- 已在 `backend/src/robot_control_backend/domain/` 中落地共享领域模型与任务状态机
- 已补充 `SemanticActionPlan`，将 Planner 产物与 Coder 产物从模型层面拆分
- 已将 `PlannerOutput`、`CoderContext`、`CoderOutput` 与最新实施计划口径对齐
- 已将规范审计对象名称收敛为 `AuditRecord`，并保留 `AuditEventRecord` 兼容别名
- 已更新 `docs/domain-models.md` 与 `docs/task-state-machine.md`
- 完成步骤 06：数据库结构与迁移策略
- 已在 `backend/src/robot_control_backend/database/` 中落地 ORM 元数据与 `pgvector` 字段类型
- 已补充 `backend/alembic/` 脚手架、`alembic.ini` 和 `20260416_01` 初始迁移
- 已补充 `docs/database-schema.md` 与 `docs/database-migration-strategy.md`
- 已更新后端 README 与 `.env` 示例，使数据库迁移配置和命令可直接审查
- 步骤 06 本地验证已通过：
  - `uv run pytest backend/tests`
  - `uv run alembic upgrade head --sql`
- 完成步骤 07：建立审计与告警数据模型
- 已在 `backend/src/robot_control_backend/domain/` 中补齐告警关联主审计事件字段
- 已在 `backend/src/robot_control_backend/database/` 中补齐 `alerts.related_audit_event_id` 外键与索引
- 已新增 `backend/src/robot_control_backend/audit/`，沉淀审计阶段、告警级别、急停升级和审计载荷禁止项规则
- 已补齐 `backend/alembic/versions/20260420_01_step07_audit_alert_models.py`
- 已补齐 `docs/audit-alert-write-rules.md`，并同步更新 `docs/domain-models.md`、`docs/database-schema.md`
- 步骤 07 本地验证已通过：
  - `uv run pytest backend/tests`
  - `uv run alembic upgrade head --sql`
- 步骤 07 已通过用户验收，允许进入步骤 08
- 完成步骤 08：实现配置管理与安全默认值
- 已在 `backend/src/robot_control_backend/bootstrap/settings.py` 中落地统一配置模块，覆盖数据库、共享模型 provider、视觉、机器人、鉴权、日志、审计、安全规则和工件存储
- 已补齐真实执行链路门禁：默认保持模拟模式，真实执行必须显式放行并补齐机器人配置、安全规则、数据库、模型密钥、急停等前置条件
- 已增强 `robot-control-config-check`，输出安全配置摘要，并支持可选数据库连通性预检与工件目录可写校验
- 已扩展 `backend/tests/test_settings.py`，覆盖安全默认值、真实执行拦截、工件目录校验和数据库预检错误识别
- 已更新 `backend/README.md` 与 `.env` 示例文件，使 Step 08 配置项、默认值和门禁规则可直接审查
- 步骤 08 本地验证已通过：
  - `uv run pytest tests -q`
  - `uv run robot-control-config-check`
- 步骤 08 已通过用户验收，允许进入步骤 09
- 完成步骤 09：实现鉴权和角色权限模型
- 已新增 `backend/src/robot_control_backend/auth/` 模块，落地操作员/管理员双角色、权限矩阵、页面访问边界和管理员专属能力定义
- 已在 API Server 中接入“服务端 Session + HTTP-only Cookie + RBAC”认证授权闭环，支持登录、登出、当前会话查询和权限矩阵查询
- 已增加受保护的权限校验接口，覆盖任务、告警查看、告警处理、机器人配置、安全规则、知识库、示教样本和审计访问边界
- 已补充 Step 09 所需引导账号配置项和示例环境文件，生产环境下要求管理员/操作员密码改为非默认值
- 已新增 `docs/auth-rbac.md`，沉淀权限矩阵、鉴权流程说明和会话管理说明
- 步骤 09 本地验证已通过：
  - `uv run pytest tests -q`
  - `uv run robot-control-config-check`
- 步骤 09 已通过用户验收，允许进入步骤 10
- 完成步骤 10：实现后端基础 API 框架
- 已在 `backend/src/robot_control_backend/api_server/` 中建立统一 API 分组、统一成功/错误响应 envelope、请求级元信息与统一异常处理
- 已将认证接口与任务、计划、告警、配置、知识、审计访问校验接口统一收敛到结构化契约，并新增 `/api/system/health`、`/api/system/version`
- 已新增 `docs/api-conventions.md`，并同步更新 `backend/README.md` 与 `memory-bank/architecture.md`
- 步骤 10 本地验证已通过：
  - `uv run pytest tests -q`
  - `uv run robot-control-config-check`
- 步骤 10 已通过用户验收，允许进入步骤 11
- 完成步骤 11：实现任务创建与查询接口
- 已新增 `backend/src/robot_control_backend/task_service/` 进程内任务服务，落地任务聚合、状态历史、审计链路和最小执行条件校验
- 已在 `backend/src/robot_control_backend/api_server/routers/tasks.py` 中实现任务创建、任务列表、任务详情与任务执行链路查询接口，并保留 `_access-check`
- 已将 Step 11 任务接口接入现有 RBAC、统一响应 envelope 和任务专用错误码
- 已新增 `backend/tests/test_tasks_api.py`，覆盖任务创建、列表、详情、执行链路、输入完整性校验、前置条件拦截、未找到与鉴权约束
- 已更新 `docs/api-conventions.md`、`docs/task-api.md`、`docs/domain-models.md` 与 `backend/README.md`
- 步骤 11 本地验证已通过：
  - `uv run pytest tests -q`
  - `uv run robot-control-config-check`
- 步骤 11 已通过用户验收，允许进入步骤 12

## 3. 下一里程碑

下一里程碑：**完成步骤 12：实现知识库、示教样本与长期记忆管理接口**

下一步目标包括：

- 实现知识库、示教样本与长期记忆管理接口
- 保持任务服务、知识/记忆接口与后续执行链路之间的契约一致性
- 为后续 RAG 检索和长期记忆写入链路保留统一元数据结构

## 4. 当前未开始事项

- 审计与告警写入服务、聚合处理和业务接口
- Worker 与模拟闭环
- 前后端联调
- 自动化测试体系完善
- 真实设备联调准备

## 5. 当前风险或阻塞项

- 前后端尚未联调，控制台仍是纯前端骨架状态
- 数据库基线虽已落地，但尚未接入真实数据库会话与业务持久化逻辑
- 当前 Step 06 / Step 07 验证以 ORM 元数据测试、规则测试和 Alembic SQL 生成验证为主，真实 PostgreSQL 空库迁移联调仍待后续环境执行
- 当前本地 `uv` 环境执行测试时使用的是 Python 3.12.7，和项目目标版本 Python 3.11 存在环境差异，后续需要在 3.11 环境再做一次确认
- 当前 Step 09 的 Session 存储为 API 进程内内存实现，数据库 `sessions` 表尚未接入持久化会话逻辑
- 当前 Step 11 已以进程内服务先落地任务业务接口，数据库 `tasks` 表与相关聚合持久化逻辑仍待后续步骤正式接入
- Worker、模拟适配器、审计/告警写入服务和长期记忆链路尚未开始，端到端闭环尚不存在

## 6. 更新规则

每完成一个“大步骤”后，必须更新本文件，包括：

- 当前阶段
- 已完成事项
- 下一里程碑
- 当前风险或阻塞项
