from __future__ import annotations

from enum import Enum
from typing import TypeVar

import sqlalchemy as sa
from sqlalchemy.types import UserDefinedType

EnumT = TypeVar("EnumT", bound=Enum)

DEFAULT_VECTOR_DIMENSIONS = 1536


def enum_values(enum_cls: type[EnumT]) -> list[str]:
    """Return the persisted values for a Python Enum."""

    return [member.value for member in enum_cls]


def sql_enum(enum_cls: type[EnumT], name: str) -> sa.Enum:
    """Create a PostgreSQL-backed SQLAlchemy Enum with stable string values."""

    return sa.Enum(
        enum_cls,
        name=name,
        values_callable=enum_values,
        native_enum=True,
        validate_strings=True,
    )


class Vector(UserDefinedType):
    """Minimal pgvector column type used by ORM metadata and Alembic migrations."""

    cache_ok = True

    def __init__(self, dimensions: int = DEFAULT_VECTOR_DIMENSIONS) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_: object) -> str:
        return f"vector({self.dimensions})"
