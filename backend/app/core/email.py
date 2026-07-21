"""
Envio de e-mail transacional (hoje, só o de redefinição de senha).

Sem SMTP configurado (`SMTP_HOST` vazio no .env), cai no modo "console
email backend": o link é apenas registrado no log do back-end — o
suficiente para desenvolver/demonstrar o fluxo completo do TCC sem
depender de um provedor de e-mail real. Configurando `SMTP_HOST` (+ usuário/
senha) no .env, passa a enviar de verdade via SMTP.
"""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("app.email")


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    subject = "Redefinição de senha — Loja Virtual"
    body = (
        f"Recebemos uma solicitação para redefinir sua senha.\n\n"
        f"Clique no link abaixo para escolher uma nova senha "
        f"(válido por {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos):\n"
        f"{reset_link}\n\n"
        f"Se você não solicitou isso, ignore este e-mail."
    )

    if not settings.SMTP_HOST:
        logger.info("[DEV] E-mail de redefinição de senha (SMTP não configurado) para %s:\n%s", to_email, body)
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