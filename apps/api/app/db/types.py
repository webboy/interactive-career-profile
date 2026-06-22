import json
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum
from sqlalchemy.types import Text, TypeDecorator


def pg_str_enum(enum_class: type[StrEnum], name: str, **kwargs) -> Enum:
    return Enum(
        enum_class,
        name=name,
        values_callable=lambda members: [member.value for member in members],
        **kwargs,
    )


class EmbeddingVector(TypeDecorator):
    """Store embeddings as pgvector on PostgreSQL and JSON text on SQLite tests."""

    impl = Text
    cache_ok = True

    def __init__(self, dimensions: int = 1536) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return list(value) if not isinstance(value, list) else value
        return json.loads(value)
