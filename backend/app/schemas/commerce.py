import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OrderStatus, PaymentMethod, PaymentStatus


class CartItemCreate(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    # Dados de exibição (produto/preço), enriquecidos pelo endpoint a partir
    # da variante — evita o front-end ter que buscar cada produto separadamente.
    sku: str | None = None
    product_name: str | None = None
    unit_price: Decimal | None = None


class CartRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    items: list[CartItemRead] = []


class OrderCreate(BaseModel):
    """Cria um pedido a partir do carrinho atual do usuário autenticado."""

    shipping_address_id: uuid.UUID
    payment_method: PaymentMethod


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    unit_price: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    shipping_address_id: uuid.UUID
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    items: list[OrderItemRead] = []


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    method: PaymentMethod
    status: PaymentStatus
    amount: Decimal
    paid_at: datetime | None
