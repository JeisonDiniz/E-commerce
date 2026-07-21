"""
Configuração central da aplicação.

Usa pydantic-settings para carregar variáveis de ambiente (.env) de forma
tipada e validada — evita `os.getenv` espalhado pelo código e falha rápido
(no boot da aplicação) se uma variável obrigatória estiver ausente.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Banco de dados
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce_ml"

    # Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    ML_PREDICTION_CACHE_TTL: int = 3600  # segundos

    # Autenticação (JWT)
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # URL do front-end, usada para montar o link de redefinição de senha
    FRONTEND_URL: str = "http://localhost:5173"
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # E-mail (opcional). Se SMTP_HOST não for configurado, o link de
    # redefinição de senha é apenas logado no console do back-end — modo
    # "console email backend", adequado para desenvolvimento/demonstração
    # do TCC sem depender de um provedor de e-mail real.
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "no-reply@loja.com"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cache simples em processo: evita reler/reparsear o .env a cada request."""
    return Settings()


settings = get_settings()
