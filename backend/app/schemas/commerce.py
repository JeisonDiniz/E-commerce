import uuid
from datetime import datetime

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
    unit_price: float | None = None


class CartRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    items: list[CartItemRead] = []


class OrderCreate(BaseModel):
    """Cria um pedido a partir do carrinho atual do usuário autenticado.

    O frete (`shipping_service`/`shipping_cost`/`shipping_deadline_days`) é
    o resultado já escolhido pelo cliente a partir de uma cotação prévia via
    `POST /shipping/quote` — o back-end confia no valor enviado aqui (é
    conferido apenas quanto à forma, não recotado), o mesmo padrão já usado
    para preço de item no carrinho.
    """

    shipping_address_id: uuid.UUID
    payment_method: PaymentMethod
    shipping_service: str
    shipping_cost: float = Field(ge=0)
    shipping_deadline_days: int | None = None


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    unit_price: float


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    shipping_address_id: uuid.UUID
    status: OrderStatus
    total_amount: float
    shipping_service: str | None = None
    shipping_cost: float = 0
    shipping_deadline_days: int | None = None
    created_at: datetime
    items: list[OrderItemRead] = []


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    method: PaymentMethod
    status: PaymentStatus
    amount: float
    paid_at: datetime | None
    installments: int | None = None
    card_brand: str | None = None
    card_last4: str | None = None
    # Só preenchidos enquanto o Pix está pendente — o front usa isso pra
    # mostrar o QR code; nunca contém dado de cartão.
    pix_qr_code: str | None = None
    pix_qr_code_base64: str | None = None


class PixPaymentCreate(BaseModel):
    order_id: uuid.UUID


class CardPaymentCreate(BaseModel):
    order_id: uuid.UUID
    # Token de uso único gerado pelo SDK do gateway NO NAVEGADOR do cliente
    # (Mercado Pago Payment Brick) — o número do cartão/CVV nunca passa por
    # aqui nem por nenhum outro campo desta API.
    token: str
    installments: int = Field(default=1, ge=1, le=12)


class PaymentStatusRead(BaseModel):
    """Resposta enxuta para o front fazer polling do status do pagamento
    enquanto aguarda a confirmação assíncrona via webhook."""

    order_status: OrderStatus
    payment_status: PaymentStatus
