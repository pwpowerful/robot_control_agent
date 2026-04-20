# 智能机械臂控制 Agent 系统 MVP 技术栈推荐

## 当前实施澄清

- 当前实现宿主机操作系统固定为 Windows。
- 当前实现不使用本地 Ollama 模型，改为通过 API 调用一个共享大语言模型。
- 实现时必须保留模型提供方抽象层，以及 API 接口与密钥隔离管理能力。
- 当前实现采用 `BaseAgent + Planner Agent + Coder Agent + Critic Agent` 的 Agent runtime 结构。
- 当前实现中 Tool 选择由 Agent 决策，Tool 路由、权限校验和安全门禁由 `Executor Worker / Orchestrator` 负责。
- 当前实现使用模拟视觉适配器和模拟机械臂适配器。
- 真实 YOLOE ONNX 模型接入和真实机械臂接入保留为后续阶段，不作为当前实现完成标准。

## 1. 结论

基于 `design_document.md` 中“单机部署、单品牌单型号机械臂、厂商 Python SDK 直连、Web 控制台、自动执行、立即停机告警”的约束，本项目 MVP 最推荐的技术栈是：

- 部署方式：**Windows 宿主机原生部署**，不在机器人执行链路上引入容器编排
- 后端主栈：**Python 3.11 + FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Psycopg 3**
- 主数据库：**PostgreSQL 16 + pgvector**
- LLM 推理：**通过 API 调用一个共享大语言模型，保留提供方抽象与密钥隔离管理**
- Agent runtime：**BaseAgent + PlannerAgent / CoderAgent / CriticAgent + Executor Worker / Orchestrator**
- 视觉运行时：**OpenCV + ONNX Runtime**
- 机器人控制：**厂商 Python SDK 直连**
- 前端控制台：**Node.js 22 LTS + React 19 + Vite 8 + TypeScript + Ant Design**
- 测试体系：**pytest + Playwright**
- 运行与审计：**Windows Service / NSSM + PostgreSQL 审计表 + JSON 日志 + 本地工件文件引用**

这是我认为当前最符合“健壮、简单、安全”的组合：组件少、数据中心化、可审计、便于单机落地，并且把安全控制放在应用层和执行层，而不是寄希望于模型“自己足够聪明”。

## 2. 选型原则

### 2.1 最少组件原则

MVP 只保留真正必要的技术组件，避免一开始就引入：

- 独立消息队列
- 独立向量数据库
- 微服务拆分
- 容器编排
- ROS/MoveIt 体系

原因很直接：当前版本是单机、单工位、单机器人，不值得用更多基础设施换更复杂的排障路径。

### 2.2 安全约束优先

系统是“自动执行真机”，因此最重要的不是模型效果炫不炫，而是：

- 指令必须结构化
- 计划必须受模板约束
- 脚本必须在白名单内
- 执行前必须做规则校验和轨迹检查
- 异常必须立即停机

因此技术栈应优先支持：

- 强类型校验
- 审计追踪
- 可控执行
- 易于回放与定位问题

### 2.3 本地优先

MVP 面向机械臂控制，延迟、稳定性和数据安全都更重要，因此执行链路、数据库、审计和视觉处理都应优先本地化；当前阶段的 LLM 保持通过共享 API 接入，但必须通过本地 Orchestrator 做超时、重试、凭据隔离和调用审计。

## 3. 推荐技术栈

| 层级 | 推荐选型 | 版本建议 | 推荐理由 |
| --- | --- | --- | --- |
| 操作系统 | Windows 11 Pro / Windows Server 2022 宿主机原生部署 | 固定主机环境 | 当前实现已锁定 Windows；后续真实机械臂 SDK、相机驱动、运动控制链路也按 Windows 兼容性优先 |
| Python 运行时 | Python | 3.11.x | 生态成熟，兼容 AI / Web / 数据栈；对本项目的后端、视觉、控制都足够稳 |
| Python 依赖管理 | uv | 当前稳定版 | 安装快、锁文件清晰、跨 Windows/Linux 一致，适合单仓库开发与部署 |
| API 框架 | FastAPI + Uvicorn | 当前稳定版 | 强类型、自动 OpenAPI 文档、WebSocket 支持好，适合任务管理、审计查询、控制台接口 |
| 数据校验 | Pydantic Validation + pydantic-settings | v2 系列 | 适合把自然语言解析结果、语义动作计划、可执行结构化计划、执行结果、审计事件与配置全部做结构化校验 |
| ORM / 数据访问 | SQLAlchemy + Psycopg | SQLAlchemy 2.0.x + Psycopg 3.x | 成熟稳定，适合事务、审计、配置、任务和记忆数据统一管理 |
| 数据库 | PostgreSQL | 16.x | 关系数据、审计日志、任务状态、配置管理都能统一承载；比拆分多套存储更稳 |
| 向量检索 | pgvector | 0.8.x | 直接挂在 PostgreSQL 上，足够支撑 SDK 文档、SOP、示教样本和经验检索；比 Milvus 更简单 |
| LLM 服务 | API 模型提供方抽象层 | 首版接入一个共享模型 | 当前环境没有本地 Ollama 模型，因此首版通过 API 构建 Agent；实现时保留 provider 抽象、凭据隔离和调用审计 |
| Agent 实现 | BaseAgent + PlannerAgent / CoderAgent / CriticAgent + Prompt 版本管理 + Pydantic 输出校验 | 不额外引入重型 Agent 框架 | 贴合设计文档中的三 Agent 结构；共享输入输出契约、审计元信息和 Tool 请求接口，同时保留完全可控的运行时边界 |
| Orchestrator | Executor Worker / Orchestrator | 当前实现自研 | 负责任务生命周期、状态流转、内部循环、Tool 路由、权限校验和安全门禁，但不替 Agent 决定调用哪个 Tool |
| 视觉运行时 | OpenCV + ONNX Runtime + 工业相机 SDK | 当前稳定版 | OpenCV 负责标定、坐标变换、ROI 和几何计算；ONNX Runtime 负责稳定推理；输出统一映射到机械臂 `base frame`，长度单位统一为 `mm`，姿态统一为 `x, y, z, rx, ry, rz` |
| 检测模型交付方式 | 沿用 PRD 中 YOLO 系列，但**运行时统一导出为 ONNX** | ONNX 模型包 | 训练与运行解耦，减少运行环境依赖，便于部署和回归 |
| 机器人执行层 | 厂商 Python SDK | 厂商官方稳定版 | 安全上最可控，也最容易获得官方支持；MVP 不建议抽象成通用机器人框架 |
| Memory Runtime | PostgreSQL + pgvector + 元数据过滤 + Top-K 检索 | 当前稳定版 | 支撑 `安全规则 -> 机械臂配置 -> SDK 白名单 -> SOP -> 示教样本 -> 长期记忆` 的读取优先级；长期记忆默认按元数据过滤后返回 `top 5` |
| 工件存储 | Windows 本地文件系统 + PostgreSQL 文件引用 | NTFS 本地目录 | 适合保存视觉截图、模型调用附件、导出日志等大体积原始工件；审计表只存结构化结果和文件引用，不直接塞大对象 |
| 前端 | React + TypeScript + Vite + Ant Design | React 19 + Vite 8 + TS 5 + Ant Design 当前稳定版 | 适合后台控制台；开发效率高、组件成熟、表格/表单/状态展示能力强 |
| 鉴权 | 服务端 Session + HTTP-only Cookie + RBAC | MVP 内置实现 | 对单机/内网控制台更简单安全；避免浏览器侧长期保存高权限 JWT |
| 服务管理 | Windows Service / NSSM | 与宿主机一致 | 当前宿主机固定为 Windows；比容器编排简单，可控且容易接入开机自启、日志、重启策略 |
| 审计与日志 | PostgreSQL 审计表 + 结构化 JSON 日志文件 + 工件引用 | 同数据库版本 | 满足“指令 -> Tool 请求 -> 语义动作计划 -> 可执行结构化计划 -> 校验 -> 执行 -> 视觉复检 -> 记忆写入”的全链路追踪；不记录 raw chain-of-thought |
| 单元 / 集成测试 | pytest | 当前稳定版 | Python 后端和执行逻辑的默认选择 |
| E2E 测试 | Playwright | 当前稳定版 | Web 控制台、任务流、告警页和审计页自动化测试简单可靠 |

## 4. 关键取舍说明

### 4.1 为什么数据库选 PostgreSQL 16 + pgvector，而不是 PostgreSQL + Milvus

推荐 **PostgreSQL 16 + pgvector**，不推荐 MVP 首版就上 Milvus。

原因：

- 任务、审计、配置、账号、记忆、RAG 元数据本来就适合关系数据库
- 向量检索量级在 MVP 阶段不会大到需要独立向量库
- 一套数据库更容易做备份、恢复、权限管理和问题排查
- 少一套服务，就少一条故障链路

这里有一个明确的工程推断：

- PostgreSQL 官方文档显示 **18 是 current**，同时 **16 仍在维护**；基于工业现场“优先成熟稳定、次优追新”的原则，我推荐 **16.x** 作为 MVP 默认版本，而不是直接上最新的 18.x

### 4.2 为什么当前首版使用 API 模型提供方，而不是本地 Ollama 或 vLLM

当前环境没有本地 Ollama 模型，因此首版推荐 **API 调用 + 提供方抽象层**。

原因：

- 当前环境可以直接落地
- 可以先完成 Agent 闭环，而不是先投入本地模型运维
- 仍可通过统一适配层控制超时、重试、凭据隔离和审计

实现要求：

- 首版只接入一个共享模型
- 必须保留 provider 抽象
- 必须隔离管理 API key
- 必须记录模型调用审计信息

不推荐首版优先 vLLM，原因是：

- 工程复杂度更高
- 对当前 MVP 的单机吞吐需求来说收益有限

### 4.3 为什么 Agent runtime 采用自研 BaseAgent，而不是重型 Agent 框架

当前设计文档已经明确：

- `Planner Agent`、`Coder Agent`、`Critic Agent` 是三个核心 Agent
- `BaseAgent` 提供共享输入输出契约与审计元信息
- Tool 选择由 Agent 决策
- Orchestrator 负责 Tool 路由和安全门禁

在这种边界下，更适合采用“原生 Python + BaseAgent 抽象 + Pydantic 输出校验”的实现方式，而不是重型 Agent 框架。

原因：

- 三个 Agent 的职责边界已经很清楚，不需要额外的编排 DSL
- 安全关键链路需要完全可控的 Tool 权限矩阵和回退规则
- 调试时需要准确看到语义动作计划、可执行结构化计划和 Tool 请求记录
- 首版不需要跨大量 Tool/Provider 的通用插件生态

### 4.4 为什么视觉运行时选 OpenCV + ONNX Runtime

这个组合比“运行时直接堆 PyTorch 训练栈”更适合 MVP：

- OpenCV 适合做相机标定、像素坐标到机械臂坐标转换、ROI、几何和基础图像处理
- ONNX Runtime 更适合部署期的稳定推理
- 模型导出为 ONNX 后，运行环境更统一

这也更符合设计文档里的 VisionTool 责任边界：它需要稳定定位和复检，而不是复杂训练平台。

另外，设计文档已经锁定：

- 最终执行坐标统一映射到机械臂 `base frame`
- 长度单位统一为 `mm`
- 姿态统一为 `x, y, z, rx, ry, rz`

因此视觉栈必须优先选择便于做标定、坐标变换和几何约束的运行时。

### 4.5 为什么不推荐在 MVP 引入 ROS / MoveIt

设计文档已经明确：

- 单品牌单型号机械臂
- 厂商 Python SDK 直连
- 不以 ROS 优先架构为目标

在这种约束下，引入 ROS / MoveIt 会带来：

- 更复杂的部署与调试
- 额外的消息和状态同步成本
- 与厂商 SDK 的二次封装成本

对 MVP 而言，这些复杂度大于收益。

### 4.6 为什么不推荐在机器人执行链路引入 Docker / Kubernetes

MVP 阶段不建议把以下进程容器化后再接真机：

- RobotTool
- 相机采集
- 运动控制
- 视觉复检

原因：

- GPU、工业相机、网卡、USB、底层驱动的直连管理更复杂
- 机器人执行问题排障会跨越宿主机、容器、驱动三层
- 对单机 MVP 来说收益很小

更稳的做法是：

- **核心控制链路宿主机原生部署**
- 后续如果需要，再把非实时模块逐步服务化或容器化

## 5. 模块落地建议

### 5.1 后端拆分方式

MVP 不做微服务，建议采用“**单仓库 + 单后端进程 + 单执行 Worker**”模式：

- `api-server`
  - 提供 Web API
  - 管理任务、配置、审计、知识库
  - 负责前端接口与状态查询
- `executor-worker`
  - 承载 `Executor Worker / Orchestrator` 与 `BaseAgent` runtime
  - 从 PostgreSQL 读取待执行任务
  - 驱动 `Planner Agent / Coder Agent / Critic Agent`
  - 按 Agent 请求路由 `VisionTool / RobotTool / Memory Layer`
  - 写回执行状态和审计记录

这样做的好处是：

- 不需要 Redis、Kafka、RabbitMQ
- 任务状态不会分散在多套系统里
- 排障时只看数据库和两个进程即可

### 5.2 任务执行模型

推荐使用 **PostgreSQL 任务表 + 行锁/状态机** 作为执行队列，而不是引入独立消息中间件。

任务状态建议至少包含：

- `created`
- `planning`
- `validating`
- `ready_to_run`
- `running`
- `verifying`
- `succeeded`
- `failed`
- `emergency_stopped`

并且建议明确内部循环规则：

- 一次完整的 `Planner Agent -> Coder Agent -> Critic Agent` 处理链路算作一次内部循环
- `Critic Agent` 补充请求 Tool 不单独计数
- 单次任务内部循环最多允许 `3` 次

### 5.3 LLM 输出约束方式

为了安全，LLM 不直接生成可自由执行的脚本，建议使用两层约束：

1. `Planner Agent` 先输出“语义动作计划”
2. `Coder Agent` 再把语义动作计划映射为“可执行结构化计划”
3. 后端根据可执行结构化计划渲染受控 SDK 脚本

然后通过：

- Pydantic 做结构化校验
- Critic Agent 做规则校验和轨迹检查
- RobotTool 只接受已放行的可执行结构化计划或其渲染脚本

这比“让模型直接写 Python 再祈祷没问题”安全得多。

### 5.4 Tool 与 Memory 运行约束

基于当前设计文档，建议技术实现层直接固化以下运行规则：

- `Planner Agent` 可请求 `VisionTool`
- `Coder Agent` 主要消费 `Memory Layer`，不直接请求 `RobotTool`
- `Critic Agent` 可补充请求 `VisionTool`
- `RobotTool` 只在 `Critic Agent` 放行后，由 `Orchestrator` 路由执行
- 长期记忆默认读取策略为“元数据过滤 + 相似度排序 + `top 5` 返回”
- 审计默认只保存结构化结果和工件引用，不将大体积原始内容直接写入审计表

### 5.5 单工位验收环境建议

为匹配当前设计文档中的单工位验收口径，建议测试与验收环境同步固定以下条件：

- 固定单工位、单机械臂型号、固定相机位姿
- 固定光照条件与背景环境
- 固定目标物料集合，共 `10` 类目标物
- 样本任务总数 `50`，默认每类目标物 `5` 个任务且均衡分布
- 允许人工复位场景，但不改变工位配置、相机位姿和安全规则

## 6. 明确不推荐的技术栈

以下技术不是不能用，而是**不建议出现在当前 MVP 首版**：

- **Milvus**
  - 当前 RAG 和记忆规模不大，`PostgreSQL + pgvector` 更简单
- **Redis + Celery**
  - 多出一套中间件和消息可见性问题；对单机执行链路收益有限
- **Kafka / RabbitMQ**
  - 对当前规模明显过重
- **ROS / MoveIt**
  - 与“厂商 SDK 直连”的 MVP 目标冲突
- **Kubernetes**
  - 对单机工控 MVP 完全过度设计
- **LangChain / LlamaIndex 重编排**
  - 首版更应该追求可控、可调、可审计，而不是堆抽象层
- **前后端多仓库**
  - 会增加联调和发布复杂度；MVP 更适合单仓库管理

## 7. 推荐的最小交付清单

如果现在就开始实施，我建议首版直接按下面的最小集合开工：

- 宿主机：Windows
- Python：3.11
- 包管理：uv
- 后端：FastAPI + Uvicorn
- 数据校验：Pydantic v2
- 数据库：PostgreSQL 16
- 向量检索：pgvector
- 数据访问：SQLAlchemy 2.0 + Psycopg 3
- LLM：一个共享模型提供方的 API 接入
- Agent runtime：BaseAgent + PlannerAgent / CoderAgent / CriticAgent
- 视觉：OpenCV + ONNX Runtime
- 工件存储：Windows 本地文件系统 + PostgreSQL 引用
- 控制台：React 19 + TypeScript + Vite 8 + Ant Design
- 测试：pytest + Playwright
- 运行管理：Windows Service / NSSM

## 8. 后续演进路线

当 MVP 通过验收后，再逐步演进：

1. 把 Vision 模块拆到独立进程或独立节点
2. 把 Agent runtime 与 Orchestrator 拆为独立服务
3. 把 Memory Runtime 拆为独立服务
4. 节点间通信改为 gRPC
5. 根据检索规模再评估是否需要独立向量数据库
6. 根据机器人型号扩展再评估是否需要抽象统一控制层

## 9. 官方参考资料

- Python 3.11 官方文档：[https://docs.python.org/3.11/](https://docs.python.org/3.11/)
- FastAPI 官方文档：[https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- SQLAlchemy 2.0 官方文档：[https://docs.sqlalchemy.org/en/20/](https://docs.sqlalchemy.org/en/20/)
- Psycopg 官方文档：[https://www.psycopg.org/](https://www.psycopg.org/)
- Alembic 官方文档：[https://alembic.sqlalchemy.org/en/latest/](https://alembic.sqlalchemy.org/en/latest/)
- PostgreSQL 官方文档：[https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)
- pgvector 官方仓库：[https://github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)
- ONNX Runtime 官方文档：[https://onnxruntime.ai/docs/](https://onnxruntime.ai/docs/)
- OpenCV 官方站点：[https://opencv.org/](https://opencv.org/)
- Node.js 官方公告：[https://nodejs.org/](https://nodejs.org/)
- React 官方文档：[https://react.dev/](https://react.dev/)
- Vite 官方文档：[https://vite.dev/guide/](https://vite.dev/guide/)
- Ant Design 官方文档：[https://ant.design/docs/react/introduce/](https://ant.design/docs/react/introduce/)
- uv 官方文档：[https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
- Playwright 官方文档：[https://playwright.dev/](https://playwright.dev/)
