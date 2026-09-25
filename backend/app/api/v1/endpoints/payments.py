import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.commerce import Order, Payment
from app.models.enums import OrderStatus, PaymentStatus
from app.models.user import User
from app.schemas.commerce import CardPaymentCreate, PaymentRead, PixPaymentCreate
from app.services.payment_service import create_card_charge, create_pix_charge

router = APIRouter(prefix="/payments", tags=["Pagamentos"])


async def _load_own_pending_payment(db: AsyncSession, order_id: uuid.UUID, user: User) -> tuple[Order, Payment]:
    """Busca o pedido + o pagamento pendente mais recente, garantindo que o
    pedido pertence ao usuário autenticado (evita que alguém pague/consulte
    o pedido de outra pessoa só por adivinhar o UUID)."""
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.payments))
    )
    order = result.scalar_one_or_none()
    if order is None or order.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido não encontrado")

    pending = [p for p in order.payments if p.status == PaymentStatus.pendente]
    if not pending:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pedido não tem pagamento pendente")
    return order, pending[-1]


@router.post("/pix", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def pay_with_pix(
    payload: PixPaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Payment:
    order, payment = await _load_own_pending_payment(db, payload.order_id, current_user)

    gateway_response = await create_pix_charge(payment, order, current_user)

    payment.gateway_payment_id = str(gateway_response["id"])
    poi = gateway_response.get("point_of_interaction", {}).get("transaction_data", {})
    payment.pix_qr_code = poi.get("qr_code")
    payment.pix_qr_code_base64 = poi.get("qr_code_base64")
    await db.commit()
    await db.refresh(payment)
    return payment


@router.post("/card", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def pay_with_card(
    payload: CardPaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Payment:
    order, payment = await _load_own_pending_payment(db, payload.order_id, current_user)

    gateway_response = await create_card_charge(payment, order, current_user, payload.token, payload.installments)

    payment.gateway_payment_id = str(gateway_response["id"])
    payment.installments = payload.installments
    card_info = gateway_response.get("card") or {}
    payment.card_brand = gateway_response.get("payment_method_id")
    payment.card_last4 = card_info.get("last_four_digits")

    status_map = {"approved": PaymentStatus.aprovado, "rejected": PaymentStatus.recusado}
    # "in_process" fica como pendente — a confirmação definitiva chega pelo
    # webhook, nunca pela resposta síncrona desta chamada.
    new_status = status_map.get(gateway_response.get("status"))
    if new_status:
        payment.status = new_status
        if new_status == PaymentStatus.aprovado:
            order.status = OrderStatus.pago

    await db.commit()
    await db.refresh(payment)
    return payment
