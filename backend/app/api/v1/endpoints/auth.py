import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.email import send_password_reset_email
from app.core.redis_client import get_redis
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import PasswordResetToken, User
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest, Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Autenticação"])

_FORGOT_PASSWORD_MAX_ATTEMPTS = 3
_FORGOT_PASSWORD_WINDOW_SECONDS = 3600


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "E-mail ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    return Token(access_token=access_token)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict[str, str]:
    """
    Sempre responde com a mesma mensagem genérica, exista ou não o e-mail —
    evita que alguém use este endpoint para descobrir quais e-mails estão
    cadastrados (enumeração de usuários).

    Também aplica rate limiting por e-mail via Redis (máx.
    `_FORGOT_PASSWORD_MAX_ATTEMPTS` solicitações por hora), para não permitir
    que alguém "bombardeie" a caixa de entrada de um usuário com e-mails de
    redefinição.
    """
    generic_response = {"message": "Se este e-mail estiver cadastrado, enviamos um link de redefinição de senha."}

    rate_limit_key = f"forgot-password:{payload.email.lower()}"
    attempts = await redis.incr(rate_limit_key)
    if attempts == 1:
        await redis.expire(rate_limit_key, _FORGOT_PASSWORD_WINDOW_SECONDS)
    if attempts > _FORGOT_PASSWORD_MAX_ATTEMPTS:
        return generic_response

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None:
        return generic_response

    # Invalida tokens anteriores ainda não usados, para não deixar vários links válidos ao mesmo tempo.
    previous = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
    )
    for token_row in previous.scalars().all():
        token_row.used_at = datetime.now(timezone.utc)

    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    db.add(PasswordResetToken(user_id=user.id, token_hash=_hash_token(raw_token), expires_at=expires_at))
    await db.commit()

    reset_link = f"{settings.FRONTEND_URL}/redefinir-senha?token={raw_token}"
    send_password_reset_email(user.email, reset_link)

    return generic_response


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    token_hash = _hash_token(payload.token)
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    token_row = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if token_row is None or token_row.used_at is not None or token_row.expires_at < now:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link de redefinição inválido ou expirado")

    user = await db.get(User, token_row.user_id)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link de redefinição inválido ou expirado")

    user.password_hash = hash_password(payload.new_password)
    token_row.used_at = now
    await db.commit()

    return {"message": "Senha redefinida com sucesso."}