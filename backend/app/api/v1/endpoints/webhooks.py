"""
Endpoint público (sem autenticação de usuário — quem chama é o Mercado
Pago, não um cliente logado) que recebe as notificações de pagamento.

A segurança aqui não vem de um JWT, e sim da validação da assinatura HMAC
do próprio gateway (ver `verify_webhook_signature`) — sem isso, qualquer um
poderia forjar um POST dizendo "pagamento aprovado".
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.commerce import Order, Payment
from app.models.enums import OrderStatus, PaymentStatus
from app.services.payment_service import fetch_payment, verify_webhook_signature

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

_GATEWAY_STATUS_MAP = {
    "approved": PaymentStatus.aprovado,
    "rejected": PaymentStatus.recusado,
    "refunded": PaymentStatus.estornado,
    "cancelled": PaymentStatus.recusado,
}


@router.post("/mercadopago", status_code=status.HTTP_200_OK)
async def mercadopago_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_signature: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
) -> dict[str, str]:
    body = await request.json()
    if body.get("type") != "payment":
        return {"status": "ignored"}

    payment_id = str(body.get("data", {}).get("id", ""))
    if not payment_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payload sem id de pagamento")

    if not x_signature or not x_request_id or not verify_webhook_signature(x_signature, x_request_id, payment_id):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Assinatura de webhook inválida")

    # Defesa em profundidade: mesmo com assinatura válida, nunca confia no
    # status vindo do payload do webhook — reconsulta a API do gateway pelo
    # ID para pegar o dado autoritativo.
    gateway_data = await fetch_payment(payment_id)

    result = await db.execute(select(Payment).where(Payment.gateway_payment_id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        # Idempotência/robustez: evento de um pagamento que não é nosso
        # (ou webhook duplicado chegando antes de gravarmos o gateway_payment_id).
        return {"status": "unknown_payment"}

    new_status = _GATEWAY_STATUS_MAP.get(gateway_data.get("status"))
    if new_status and payment.status != new_status:
        payment.status = new_status
        if new_status == PaymentStatus.aprovado:
            order = await db.get(Order, payment.order_id)
            if order is not None:
                order.status = OrderStatus.pago
        await db.commit()

    return {"status": "processed"}
