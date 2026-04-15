# AGENTS.md

## Project Overview

This workspace contains product documentation for an intelligent robotic arm control Agent MVP.

Current source-of-truth documents:

- `design_document.md`: MVP product design and functional scope
- `tech_stack.md`: recommended MVP technology stack

The project goal is to build a **single-workstation MVP** that closes the loop from natural-language instruction to safe robotic execution.

## MVP Scope

- Single workstation deployment
- Single robot brand and single model
- Web console as the primary operator interface
- Vendor Python SDK direct integration
- Automatic execution only after validation passes
- Immediate stop and alert on anomalies
- Vision verification after execution
- Long-term memory write only after successful visual verification

Out of scope for MVP:

- Multi-brand robot support
- Multi-workstation orchestration
- ROS-first architecture
- Full digital twin simulation
- Automatic retry on failure
- Heavy microservice decomposition

## Preferred Technical Stack

- Backend: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0, Psycopg 3
- Database: PostgreSQL 16 with pgvector
- LLM runtime: Ollama local service
- Vision runtime: OpenCV + ONNX Runtime
- Frontend: React 19, TypeScript, Vite, Ant Design
- Service model: host-native deployment, not container orchestration on the robot control path
- Process layout: monorepo, one API server plus one executor worker

Do not introduce these in MVP unless explicitly approved:

- Milvus
- Redis/Celery
- Kafka/RabbitMQ
- ROS/MoveIt
- Kubernetes
- LangChain/LlamaIndex or other heavy agent orchestration frameworks

## Safety Rules

- Never allow free-form model-generated Python to execute directly on the robot
- LLM output must be converted into structured plans first
- Execution must be limited to whitelisted motion/action templates
- Validation must include syntax, workspace, reachability, joint-limit, and collision checks
- Dangerous detections such as human-hand intrusion must trigger immediate stop
- Failed tasks must never write to long-term memory
- Auditability is mandatory for instruction, plan, validation, execution, verification, and memory write

## Implementation Priorities

1. Build the core task lifecycle and audit trail
2. Implement structured planning and validation before any real execution
3. Keep the execution path simple and deterministic
4. Prefer local and synchronous components over distributed complexity
5. Add abstractions only when a real second robot/model or node split is required

## Suggested Module Boundaries

- `api-server`: web APIs, auth, task management, audit queries, config management
- `executor-worker`: task execution pipeline, planner/coder/critic orchestration
- `vision`: detection, coordinate transformation, visual verification
- `robot_adapter`: vendor SDK wrapper and emergency stop handling
- `knowledge_memory`: RAG retrieval, samples, long-term memory write rules

## Working Conventions

- Prefer simple, explicit, debuggable implementations over flexible abstractions
- Prefer one database over multiple persistence systems in MVP
- Keep task states explicit and queryable
- Treat safety and auditability as product requirements, not implementation details
- When in doubt, preserve the constraints in `design_document.md` and `tech_stack.md`
## Important prompt
写任何代码前都必须完整阅读memory-bank/@design_document.md
写任何代码前都必须完整阅读memory-bank/@architecture.md
没完成一个重大功能或里程碑后，必须更新memory-bank/@architecture.md