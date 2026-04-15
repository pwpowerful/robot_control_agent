# 智能机械臂控制 Agent 系统 MVP 技术栈推荐

## 1. 结论

基于 `design_document.md` 中“单机部署、单品牌单型号机械臂、厂商 Python SDK 直连、Web 控制台、自动执行、立即停机告警”的约束，本项目 MVP 最推荐的技术栈是：

- 部署方式：**宿主机原生部署**，不在机器人执行链路上引入容器编排
- 后端主栈：**Python 3.11 + FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Psycopg 3**
- 主数据库：**PostgreSQL 16 + pgvector**
- LLM 推理：**Ollama 本地推理服务**
- 视觉运行时：**OpenCV + ONNX Runtime**
- 机器人控制：**厂商 Python SDK 直连**
- 前端控制台：**Node.js 22 LTS + React 19 + Vite 8 + TypeScript + Ant Design**
- 测试体系：**pytest + Playwright**
- 运行与审计：**systemd 管理服务 + PostgreSQL 审计表 + JSON 日志**

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

MVP 面向机械臂控制，延迟、稳定性和数据安全都更重要，因此推理、数据库、审计、视觉处理都应优先本地化。

## 3. 推荐技术栈

| 层级 | 推荐选型 | 版本建议 | 推荐理由 |
| --- | --- | --- | --- |
| 操作系统 | Ubuntu 22.04 LTS 宿主机原生部署；若厂商 SDK 仅支持 Windows，则用 Windows 11 Pro / Windows Server 2022 | 固定主机环境 | 机器人 SDK、GPU、相机驱动、运动控制链路更适合直接运行在宿主机；避免 Docker 对 USB、驱动、实时访问造成额外复杂度 |
| Python 运行时 | Python | 3.11.x | 生态成熟，兼容 AI / Web / 数据栈；对本项目的后端、视觉、控制都足够稳 |
| Python 依赖管理 | uv | 当前稳定版 | 安装快、锁文件清晰、跨 Windows/Linux 一致，适合单仓库开发与部署 |
| API 框架 | FastAPI + Uvicorn | 当前稳定版 | 强类型、自动 OpenAPI 文档、WebSocket 支持好，适合任务管理、审计查询、控制台接口 |
| 数据校验 | Pydantic Validation | v2 系列 | 适合把自然语言解析结果、计划对象、执行结果、审计事件全部做结构化校验 |
| ORM / 数据访问 | SQLAlchemy + Psycopg | SQLAlchemy 2.0.x + Psycopg 3.x | 成熟稳定，适合事务、审计、配置、任务和记忆数据统一管理 |
| 数据库 | PostgreSQL | 16.x | 关系数据、审计日志、任务状态、配置管理都能统一承载；比拆分多套存储更稳 |
| 向量检索 | pgvector | 0.8.x | 直接挂在 PostgreSQL 上，足够支撑 SDK 文档、SOP、示教样本和经验检索；比 Milvus 更简单 |
| LLM 服务 | Ollama | 当前稳定版 | 本地部署最简单，API 清晰，适合单机 MVP；后端可直接通过 HTTP 调用 |
| Agent 实现 | 原生 Python 服务 + Prompt 模板 + Pydantic 输出校验 | 不额外引入重型 Agent 框架 | 安全关键链路要可控、可调试、可审计；不建议首版上 LangChain / LlamaIndex 这类重编排框架 |
| 视觉运行时 | OpenCV + ONNX Runtime + 工业相机 SDK | 当前稳定版 | OpenCV 负责标定、坐标变换、ROI 和几何计算；ONNX Runtime 负责稳定推理；运行时比直接堆训练框架更稳 |
| 检测模型交付方式 | 沿用 PRD 中 YOLO 系列，但**运行时统一导出为 ONNX** | ONNX 模型包 | 训练与运行解耦，减少运行环境依赖，便于部署和回归 |
| 机器人执行层 | 厂商 Python SDK | 厂商官方稳定版 | 安全上最可控，也最容易获得官方支持；MVP 不建议抽象成通用机器人框架 |
| 前端 | React + TypeScript + Vite + Ant Design | React 19 + Vite 8 + TS 5 + Ant Design 当前稳定版 | 适合后台控制台；开发效率高、组件成熟、表格/表单/状态展示能力强 |
| 鉴权 | 服务端 Session + HTTP-only Cookie + RBAC | MVP 内置实现 | 对单机/内网控制台更简单安全；避免浏览器侧长期保存高权限 JWT |
| 服务管理 | systemd；Windows 备用为 Windows Service / NSSM | 与宿主机一致 | 比容器编排简单，可控且容易接入开机自启、日志、重启策略 |
| 审计与日志 | PostgreSQL 审计表 + 结构化 JSON 日志文件 | 同数据库版本 | 满足“指令 -> 计划 -> 校验 -> 执行 -> 视觉复检 -> 记忆写入”的全链路追踪 |
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

### 4.2 为什么 LLM 服务选 Ollama，而不是一开始就上 vLLM 或云端 API

推荐 **Ollama 本地部署**，原因是：

- 单机部署最简单
- 本地 HTTP API 易于集成
- 模型切换和管理成本低
- 更符合机器人控制场景对本地化与稳定性的偏好

不推荐首版优先云端 API，原因是：

- 增加外网依赖
- 数据外发和网络抖动风险更大
- 自动执行链路的稳定性更难兜底

不推荐首版优先 vLLM，原因是：

- 工程复杂度更高
- 对当前 MVP 的单机吞吐需求来说收益有限

### 4.3 为什么视觉运行时选 OpenCV + ONNX Runtime

这个组合比“运行时直接堆 PyTorch 训练栈”更适合 MVP：

- OpenCV 适合做相机标定、像素坐标到机械臂坐标转换、ROI、几何和基础图像处理
- ONNX Runtime 更适合部署期的稳定推理
- 模型导出为 ONNX 后，运行环境更统一

这也更符合设计文档里的 VisionTool 责任边界：它需要稳定定位和复检，而不是复杂训练平台。

### 4.4 为什么不推荐在 MVP 引入 ROS / MoveIt

设计文档已经明确：

- 单品牌单型号机械臂
- 厂商 Python SDK 直连
- 不以 ROS 优先架构为目标

在这种约束下，引入 ROS / MoveIt 会带来：

- 更复杂的部署与调试
- 额外的消息和状态同步成本
- 与厂商 SDK 的二次封装成本

对 MVP 而言，这些复杂度大于收益。

### 4.5 为什么不推荐在机器人执行链路引入 Docker / Kubernetes

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
  - 从 PostgreSQL 读取待执行任务
  - 调用 VisionTool、Planner、Coder、Critic、RobotTool
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

### 5.3 LLM 输出约束方式

为了安全，LLM 不直接生成可自由执行的脚本，建议使用两层约束：

1. LLM 先输出结构化任务计划
2. 后端再把计划映射为受控动作模板

然后通过：

- Pydantic 做结构化校验
- Critic 做规则校验和轨迹检查
- RobotTool 只接受白名单动作

这比“让模型直接写 Python 再祈祷没问题”安全得多。

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

- 宿主机：Ubuntu 22.04 LTS
- Python：3.11
- 包管理：uv
- 后端：FastAPI + Uvicorn
- 数据校验：Pydantic v2
- 数据库：PostgreSQL 16
- 向量检索：pgvector
- 数据访问：SQLAlchemy 2.0 + Psycopg 3
- LLM：Ollama
- 视觉：OpenCV + ONNX Runtime
- 控制台：React 19 + TypeScript + Vite 8 + Ant Design
- 测试：pytest + Playwright
- 运行管理：systemd

## 8. 后续演进路线

当 MVP 通过验收后，再逐步演进：

1. 把 Vision 模块拆到独立进程或独立节点
2. 把 Agent / Executor 拆为独立服务
3. 节点间通信改为 gRPC
4. 根据检索规模再评估是否需要独立向量数据库
5. 根据机器人型号扩展再评估是否需要抽象统一控制层

## 9. 官方参考资料

- Python 3.11 官方文档：[https://docs.python.org/3.11/](https://docs.python.org/3.11/)
- FastAPI 官方文档：[https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- SQLAlchemy 2.0 官方文档：[https://docs.sqlalchemy.org/en/20/](https://docs.sqlalchemy.org/en/20/)
- Psycopg 官方文档：[https://www.psycopg.org/](https://www.psycopg.org/)
- Alembic 官方文档：[https://alembic.sqlalchemy.org/en/latest/](https://alembic.sqlalchemy.org/en/latest/)
- PostgreSQL 官方文档：[https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)
- pgvector 官方仓库：[https://github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)
- Ollama 官方文档：[https://docs.ollama.com/](https://docs.ollama.com/)
- ONNX Runtime 官方文档：[https://onnxruntime.ai/docs/](https://onnxruntime.ai/docs/)
- OpenCV 官方站点：[https://opencv.org/](https://opencv.org/)
- Node.js 官方公告：[https://nodejs.org/](https://nodejs.org/)
- React 官方文档：[https://react.dev/](https://react.dev/)
- Vite 官方文档：[https://vite.dev/guide/](https://vite.dev/guide/)
- Ant Design 官方文档：[https://ant.design/docs/react/introduce/](https://ant.design/docs/react/introduce/)
- uv 官方文档：[https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
- Playwright 官方文档：[https://playwright.dev/](https://playwright.dev/)
