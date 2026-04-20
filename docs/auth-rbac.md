# 鉴权与角色权限模型说明

本文对应实施计划步骤 09，描述当前版本已落地的认证方式、会话管理方式和 RBAC 权限矩阵。

## 1. 当前实现边界

- 当前认证方式为：服务端 Session + HTTP-only Cookie + RBAC。
- 当前只实现两类角色：
  - `operator`
  - `admin`
- 当前用户来源为配置文件中的引导账号，而不是数据库中的正式用户管理流程。
- 当前 Session 存储为 API 进程内内存实现，用于先锁定登录契约和权限边界。
- 数据库中的 `users`、`roles`、`user_roles`、`sessions` 表结构已在步骤 06 建好，但当前步骤尚未接入数据库持久化会话。

## 2. 登录与会话流程

当前登录流程如下：

1. 控制台向 `POST /api/auth/login` 提交用户名和密码。
2. 后端根据 `RCA_AUTH_ADMIN_*` 和 `RCA_AUTH_OPERATOR_*` 引导账号配置校验身份。
3. 登录成功后，后端在服务端创建 Session，并向浏览器返回 HTTP-only Cookie。
4. 后续请求由后端从 Cookie 中解析 Session，再判定用户角色和权限。
5. 登出时调用 `POST /api/auth/logout`，后端撤销 Session 并删除 Cookie。

当前 Cookie 行为受以下配置控制：

- `RCA_AUTH_SESSION_COOKIE_NAME`
- `RCA_AUTH_SESSION_TTL_MINUTES`
- `RCA_AUTH_REQUIRE_SECURE_COOKIES`
- `RCA_AUTH_COOKIE_SAME_SITE`

## 3. 角色定义

### 3.1 操作员

操作员负责一线任务执行相关操作，当前允许：

- 创建任务
- 查看任务列表和任务详情
- 查看执行计划、执行结果和告警

操作员当前不允许：

- 修改机器人配置
- 修改安全规则
- 维护知识库条目
- 维护示教样本
- 处理告警
- 查看审计日志

### 3.2 管理员

管理员包含操作员全部能力，并额外允许：

- 管理机器人配置
- 管理安全规则
- 管理知识库条目
- 管理示教样本
- 处理告警
- 查看全量审计日志

## 4. 权限矩阵

### 4.1 页面权限

| 页面区域 | operator | admin |
| --- | --- | --- |
| 任务列表 | 允许 | 允许 |
| 任务详情 | 允许 | 允许 |
| 告警中心 | 允许查看 | 允许查看与处理 |
| 机器人配置 | 禁止 | 允许 |
| 安全规则配置 | 禁止 | 允许 |
| 知识库条目 | 禁止 | 允许 |
| 示教样本 | 禁止 | 允许 |
| 审计日志 | 禁止 | 允许 |

### 4.2 接口权限

当前已落地的受保护接口边界如下：

| 接口 | operator | admin |
| --- | --- | --- |
| `GET /api/tasks/_access-check` | 允许 | 允许 |
| `GET /api/alerts/_access-check` | 允许 | 允许 |
| `POST /api/alerts/_handle-check` | 禁止 | 允许 |
| `POST /api/config/robot/_access-check` | 禁止 | 允许 |
| `POST /api/config/safety-rules/_access-check` | 禁止 | 允许 |
| `POST /api/knowledge/items/_access-check` | 禁止 | 允许 |
| `POST /api/knowledge/samples/_access-check` | 禁止 | 允许 |
| `GET /api/audit/_access-check` | 禁止 | 允许 |

### 4.3 数据操作权限

| 数据操作 | operator | admin |
| --- | --- | --- |
| 创建任务 | 允许 | 允许 |
| 查看任务状态 | 允许 | 允许 |
| 查看执行计划/结果 | 允许 | 允许 |
| 查看告警 | 允许 | 允许 |
| 处理告警 | 禁止 | 允许 |
| 修改机器人配置 | 禁止 | 允许 |
| 修改安全规则 | 禁止 | 允许 |
| 维护知识库条目 | 禁止 | 允许 |
| 维护示教样本 | 禁止 | 允许 |

### 4.4 审计查看权限

- `operator`：无审计查看权限
- `admin`：拥有全量审计查看权限

## 5. 当前验证口径

步骤 09 当前重点验证以下行为：

- 未登录用户不能访问受保护业务接口
- 操作员不能访问管理员专属配置、知识库和审计能力
- 管理员可以访问全量配置、告警处理和审计能力
- 登录后会下发 HTTP-only Cookie
- 登出后当前 Session 会被撤销

## 6. 后续演进方向

后续步骤会在保持当前接口契约不变的前提下继续演进：

- 接入数据库会话与正式用户/角色持久化
- 将权限保护接入真实业务接口而不仅是访问校验端点
- 将页面权限接入前端控制台导航与路由守卫
