"""
Base declarativa e mixins reutilizados por todos os models SQLAlchemy.

IMPORTANTE: o schema do banco é criado a partir de `database/schema.sql`
(DDL "puro", executado uma vez via psql/migração inicial) — não a partir de
`Base.metadata.create_all()`. Os models abaixo apenas *mapeiam* essas
tabelas para uso via ORM na aplicação. Isso mantém o SQL como fonte única
de verdade da estrutura do banco (mais fácil de revisar/versionar/discutir
na defesa do TCC) e o ORM como camada de conveniência para consultas.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UUIDPKMixin:
    """PK em UUID, com default gerado no próprio Postgres (gen_random_uuid())."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )


class TimestampMixin:
    """created_at / updated_at padronizados, preenchidos pelo servidor."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )