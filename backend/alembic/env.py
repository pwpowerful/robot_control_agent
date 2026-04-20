from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import dotenv_values
from sqlalchemy import engine_from_config, pool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from robot_control_backend.database import Base  # noqa: E402
from robot_control_backend.database import models as _database_models  # noqa: F401,E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolve_database_url() -> str:
    database_url = os.getenv("RCA_DATABASE_URL")
    app_env = os.getenv("RCA_APP_ENV", "development")

    if database_url:
        return database_url

    # Match backend settings precedence: environment-specific file overrides shared defaults.
    for candidate in (PROJECT_ROOT / f".env.{app_env}", PROJECT_ROOT / ".env"):
        if candidate.exists():
            values = dotenv_values(candidate)
            database_url = values.get("RCA_DATABASE_URL")
            if database_url:
                return database_url

    raise RuntimeError(
        "RCA_DATABASE_URL must be set before running Alembic migrations or offline SQL generation."
    )


def run_migrations_offline() -> None:
    context.configure(
        url=_resolve_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _resolve_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
