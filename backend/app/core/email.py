"""
Envio de e-mail transacional (redefinição de senha + ciclo de vida do pedido).

Sem SMTP configurado (`SMTP_HOST` vazio no .env), cai no modo "console
email backend": o conteúdo é apenas registrado no log do back-end — o
suficiente para desenvolver/demonstrar o fluxo completo do TCC sem
depender de um provedor de e-mail real. Configurando `SMTP_HOST` (+ usuário/
senha) no .env, passa a enviar de verdade via SMTP.
"""
import asyncio
import logging
import smtplib
import uuid
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("app.email")


def _deliver(to_email: str, subject: str, body: str) -> None:
    """Parte síncrona (bloqueante) do envio — só deve ser chamada via `_send`."""
    if not settings.SMTP_HOST:
        logger.info("[DEV] E-mail (SMTP não configurado) para %s — %s:\n%s", to_email, subject, body)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)


async def _send(to_email: str, subject: str, body: str) -> None:
    """`smtplib` é bloqueante (I/O de socket síncrono) — roda em thread separada
    pra não travar o event loop do FastAPI durante a conexão SMTP.

    Falha de e-mail é tratada como "best effort": nunca deve derrubar o
    checkout, a confirmação de pagamento ou o processamento de um webhook só
    porque o provedor SMTP está fora do ar — só loga o erro.
    """
    try:
        await asyncio.to_thread(_deliver, to_email, subject, body)
    except Exception:
        logger.exception("Falha ao enviar e-mail para %s (assunto: %s)", to_email, subject)


def _short_id(order_id: uuid.UUID) -> str:
    """Referência curta e legível do pedido pro corpo do e-mail (não é usada pra buscar no banco)."""
    return str(order_id)[:8]


async def send_password_reset_email(to_email: str, reset_link: str) -> None:
    subject = "Redefinição de senha — Loja Virtual"
    body = (
        f"Recebemos uma solicitação para redefinir sua senha.\n\n"
        f"Clique no link abaixo para escolher uma nova senha "
        f"(válido por {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos):\n"
        f"{reset_link}\n\n"
        f"Se você não solicitou isso, ignore este e-mail."
    )
    await _send(to_email, subject, body)


async def send_order_confirmation_email(to_email: str, order_id: uuid.UUID, total_amount: float) -> None:
    ref = _short_id(order_id)
    subject = f"Pedido #{ref} confirmado — Loja Virtual"
    body = (
        f"Recebemos seu pedido #{ref}!\n\n"
        f"Total: R$ {total_amount:.2f}\n\n"
        f"Assim que o pagamento for aprovado, você recebe um novo e-mail de confirmação. "
        f"Acompanhe o status a qualquer momento em \"Meus pedidos\" no site."
    )
    await _send(to_email, subject, body)


async def send_payment_approved_email(to_email: str, order_id: uuid.UUID, total_amount: float) -> None:
    ref = _short_id(order_id)
    subject = f"Pagamento aprovado — Pedido #{ref}"
    body = (
        f"Boas notícias! O pagamento do seu pedido #{ref} (R$ {total_amount:.2f}) foi aprovado.\n\n"
        f"Já estamos preparando tudo para o envio."
    )
    await _send(to_email, subject, body)


async def send_order_shipped_email(
    to_email: str,
    order_id: uuid.UUID,
    shipping_service: str | None,
    shipping_deadline_days: int | None,
) -> None:
    ref = _short_id(order_id)
    servico = f" pela transportadora {shipping_service}" if shipping_service else ""
    prazo = f" — previsão de entrega em até {shipping_deadline_days} dia(s) útil(eis)" if shipping_deadline_days else ""
    subject = f"Pedido #{ref} enviado — Loja Virtual"
    body = f"Seu pedido #{ref} foi enviado{servico}{prazo}.\n\nAcompanhe o status em \"Meus pedidos\" no site."
    await _send(to_email, subject, body)
