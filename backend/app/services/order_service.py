"""
Fluxo de checkout: carrinho -> pedido -> baixa de estoque -> pagamento.

Mantido em um único service (em vez de espalhar pelo router) porque é uma
transação com múltiplos efeitos colaterais que precisam ser atômicos:
se qualquer passo falhar (ex: item sem estoque), nada deve ser persistido.
"""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.email import send_order_confirmation_email
from app.models.commerce import Cart, Order, OrderItem, Payment
from app.models.enums import MovementType, PaymentMethod, PaymentStatus
from app.models.catalog import ProductVariant
from app.models.user import User
from app.services.inventory_service import apply_movement


async def checkout(
    db: AsyncSession,
    user_id: uuid.UUID,
    shipping_address_id: uuid.UUID,
    payment_method: PaymentMethod,
    shipping_service: str,
    shipping_cost: float,
    shipping_deadline_days: int | None = None,
) -> Order:
    result = await db.execute(
        select(Cart).where(Cart.user_id == user_id).options(selectinload(Cart.items))
    )
    cart = result.scalar_one_or_none()
    if cart is None or not cart.items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Carrinho vazio")

    order = Order(
        user_id=user_id,
        shipping_address_id=shipping_address_id,
        total_amount=0,
        shipping_service=shipping_service,
        shipping_cost=shipping_cost,
        shipping_deadline_days=shipping_deadline_days,
    )
    db.add(order)
    await db.flush()  # garante order.id antes de criar os itens

    total = 0
    for cart_item in cart.items:
        variant = await db.get(ProductVariant, cart_item.variant_id)
        if variant is None or not variant.active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Produto indisponível no carrinho")

        unit_price = variant.price
        order_item = OrderItem(
            order_id=order.id,
            variant_id=variant.id,
            quantity=cart_item.quantity,
            unit_price=unit_price,
        )
        db.add(order_item)
        total += float(unit_price) * cart_item.quantity

        # Baixa de estoque associada a esta venda (auditável via reference_order_id).
        await apply_movement(
            db,
            variant_id=variant.id,
            movement_type=MovementType.saida,
            quantity=cart_item.quantity,
            reason="venda",
            reference_order_id=order.id,
            created_by=user_id,
        )

    order.total_amount = total + shipping_cost

    payment = Payment(
        order_id=order.id,
        method=payment_method,
        status=PaymentStatus.pendente,
        amount=order.total_amount,
    )
    db.add(payment)

    # Carrinho é esvaziado após a conversão em pedido.
    for cart_item in list(cart.items):
        await db.delete(cart_item)

    await db.commit()
    await db.refresh(order)

    # E-mail é "best effort" (ver app/core/email.py): nunca deve impedir o
    # checkout de concluir, mesmo se o envio falhar.
    user = await db.get(User, user_id)
    if user is not None:
        await send_order_confirmation_email(user.email, order.id, float(order.total_amount))

    return order