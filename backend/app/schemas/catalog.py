import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import GenderType, SeasonType, SizeType


class CategoryCreate(BaseModel):
    name: str
    slug: str
    parent_id: uuid.UUID | None = None


class CategoryRead(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class ProductVariantCreate(BaseModel):
    sku: str
    size: SizeType
    color: str
    price: Decimal
    cost_price: Decimal | None = None


class ProductVariantRead(ProductVariantCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    active: bool
    # saldo atual em estoque, populado a partir do relacionamento `inventory`
    stock_quantity: int | None = None


class ProductCreate(BaseModel):
    category_id: uuid.UUID
    name: str
    description: str | None = None
    brand: str | None = None
    gender: GenderType = GenderType.unissex
    season: SeasonType = SeasonType.o_ano_todo
    base_price: Decimal
    variants: list[ProductVariantCreate] = []


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    brand: str | None = None
    gender: GenderType | None = None
    season: SeasonType | None = None
    base_price: Decimal | None = None
    active: bool | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    description: str | None
    brand: str | None
    gender: GenderType
    season: SeasonType
    base_price: Decimal
    active: bool
    variants: list[ProductVariantRead] = []
