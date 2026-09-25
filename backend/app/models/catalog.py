import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import GenderType, SeasonType, SizeType, pg_enum


class Category(UUIDPKMixin, Base):
    __tablename__ = "categories"

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "products"

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gender: Mapped[GenderType] = mapped_column(
        pg_enum(GenderType, "gender_type"), nullable=False, default=GenderType.unissex
    )
    season: Mapped[SeasonType] = mapped_column(
        pg_enum(SeasonType, "season_type"), nullable=False, default=SeasonType.o_ano_todo
    )
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    category: Mapped["Category"] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.sort_order"
    )


class ProductVariant(UUIDPKMixin, TimestampMixin, Base):
    """Combinação vendável de tamanho/cor de um produto — unidade real de estoque e venda."""

    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("product_id", "size", "color"),)

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    size: Mapped[SizeType] = mapped_column(pg_enum(SizeType, "size_type"), nullable=False)
    color: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    cost_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    # Peso/dimensões da embalagem — usados para cotar frete (Melhor Envio).
    weight_grams: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    height_cm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=3)
    width_cm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=25)
    length_cm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=35)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    product: Mapped["Product"] = relationship(back_populates="variants")
    inventory: Mapped["Inventory"] = relationship(back_populates="variant", uselist=False, cascade="all, delete-orphan")


class ProductImage(UUIDPKMixin, Base):
    """Foto de produto associada a uma cor (color=None = imagem geral/fallback).

    `storage_key` é uma chave relativa (não uma URL/caminho absoluto) —
    a URL final é resolvida em tempo de leitura via StorageBackend
    (app/core/storage.py), o que permite trocar de disco local para um
    provedor de nuvem no deploy sem alterar os registros já salvos.
    """

    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="images")