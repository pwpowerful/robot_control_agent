# Docs Directory

This directory is for additional documentation beyond the core memory-bank.

## Responsibilities
- API Documentation: Generated OpenAPI docs or manual API references.
- User Guides: Instructions for operators and administrators.
- Deployment Guides: Detailed setup and maintenance instructions.
- Architecture Diagrams: Visual representations of the system (if not in memory-bank).
- Changelog: Version history and release notes.

Note: Core project documentation is maintained in the `memory-bank/` directory at the root level, including design documents, implementation plans, and architecture truths. This `docs/` directory is for supplementary or generated docs.

## Current Files

- `api-conventions.md`: Step 10 and Step 11 API envelope, error, and endpoint conventions.
- `task-api.md`: Step 11 task API behavior, permissions, and prerequisite rules.
- `auth-rbac.md`: Step 09 RBAC matrix and session conventions.
- `domain-models.md`: shared domain model baseline plus Step 11 task status history notes.
- `task-state-machine.md`: shared task lifecycle rules.
- `audit-alert-write-rules.md`: Step 07 audit and alert write policy baseline.
- `database-schema.md`: current PostgreSQL schema baseline.
- `database-migration-strategy.md`: Alembic and migration strategy notes.
