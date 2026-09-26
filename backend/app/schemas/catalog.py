import uuid

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
    # Opcional: se não informado, o back-end gera um SKU único sozinho (ver
    # products.py::_generate_sku) — evita que o cadastro trave por causa de
    # um SKU digitado errado ou repetido sem querer, num campo que quem
    # cadastra roupa manualmente não tem motivo forte pra escolher à mão.
    sku: str | None = None
    size: SizeType
    color: str
    price: float
    cost_price: float | None = None
    # Peso/dimensões da embalagem — usados para cotar frete (Melhor Envio).
    # Padrões razoáveis para uma peça de roupa dobrada.
    weight_grams: int = 300
    height_cm: float = 3
    width_cm: float = 25
    length_cm: float = 35


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
    base_price: float
    variants: list[ProductVariantCreate] = []


class ProductImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    color: str | None
    alt_text: str | None
    sort_order: int
    is_primary: bool
    # Resolvida a partir de storage_key + StorageBackend no endpoint (nunca
    # populada via from_attributes — o model não expõe essa propriedade,
    # só a storage_key interna) — nunca exposta como caminho de arquivo em disco.
    url: str = ""


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    brand: str | None = None
    gender: GenderType | None = None
    season: SeasonType | None = None
    base_price: float | None = None
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
    base_price: float
    active: bool
    variants: list[ProductVariantRead] = []
    images: list[ProductImageRead] = []
