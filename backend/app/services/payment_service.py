"""
Integração com o Mercado Pago: criação de cobrança Pix/cartão e validação
de assinatura de webhook.

Isolado em service para manter os endpoints (`api/v1/endpoints/payments.py`,
`webhooks.py`) finos e para o job de reconciliação (`scripts/`) poder
reusar `fetch_payment` sem duplicar a chamada HTTP.

Segurança: em nenhum ponto deste módulo — nem em nenhum outro do projeto —
um número de cartão, CVV ou validade é lido, armazenado ou logado. O
cartão é tokenizado inteiramente no navegador do cliente (SDK JS do
Mercado Pago); aqui só circula o token de uso único.
"""
import hashlib
import hmac

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.commerce import Order, Payment
from app.models.user import User


def _client() -> httpx.AsyncClient:
    if not settings.MERCADO_PAGO_ACCESS_TOKEN:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Pagamento indisponível: MERCADO_PAGO_ACCESS_TOKEN não configurado.",
        )
    return httpx.AsyncClient(
        base_url=settings.MERCADO_PAGO_BASE_URL,
        headers={"Authorization": f"Bearer {settings.MERCADO_PAGO_ACCESS_TOKEN}"},
        timeout=15,
    )


async def create_pix_charge(payment: Payment, order: Order, user: User) -> dict:
    async with _client() as client:
        response = await client.post(
            "/v1/payments",
            # X-Idempotency-Key evita criar duas cobranças caso o cliente
            # clique duas vezes/o request seja reenviado por instabilidade.
            headers={"X-Idempotency-Key": str(payment.id)},
            json={
                "transaction_amount": float(payment.amount),
                "description": f"Pedido {order.id}",
                "payment_method_id": "pix",
                "payer": {"email": user.email, "first_name": user.name.split(" ")[0]},
            },
        )
    if response.status_code >= 400:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Mercado Pago recusou o Pix: {response.text[:300]}")
    return response.json()


async def create_card_charge(payment: Payment, order: Order, user: User, token: str, installments: int) -> dict:
    async with _client() as client:
        response = await client.post(
            "/v1/payments",
            headers={"X-Idempotency-Key": str(payment.id)},
            json={
                "transaction_amount": float(payment.amount),
                "token": token,
                "description": f"Pedido {order.id}",
                "installments": installments,
                "payment_method_id": None,  # o Mercado Pago infere a partir do token
                "payer": {"email": user.email},
            },
        )
    if response.status_code >= 400:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Mercado Pago recusou o cartão: {response.text[:300]}")
    return response.json()


async def fetch_payment(gateway_payment_id: str) -> dict:
    """Reconsulta o pagamento direto na API — nunca confiar só no payload
    de um webhook, que pode ser forjado se a assinatura não for validada
    (defesa em profundidade: valida a assinatura E reconsulta)."""
    async with _client() as client:
        response = await client.get(f"/v1/payments/{gateway_payment_id}")
    response.raise_for_status()
    return response.json()


def verify_webhook_signature(x_signature: str, x_request_id: str, data_id: str) -> bool:
    """Recria a assinatura HMAC conforme a documentação do Mercado Pago e
    compara em tempo constante. Um webhook com assinatura inválida deve
    ser rejeitado ANTES de qualquer leitura/gravação no banco — do
    contrário, qualquer um poderia forjar um POST dizendo "pagamento
    aprovado" para o endpoint público de webhook.
    """
    if not settings.MERCADO_PAGO_WEBHOOK_SECRET:
        return False
    try:
        parts = dict(part.split("=", 1) for part in x_signature.split(","))
        manifest = f"id:{data_id};request-id:{x_request_id};ts:{parts['ts']};"
        expected = hmac.new(
            settings.MERCADO_PAGO_WEBHOOK_SECRET.encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, parts["v1"])
    except (KeyError, ValueError):
        return False
