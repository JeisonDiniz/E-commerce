"""
Configuração central da aplicação.

Usa pydantic-settings para carregar variáveis de ambiente (.env) de forma
tipada e validada — evita `os.getenv` espalhado pelo código e falha rápido
(no boot da aplicação) se uma variável obrigatória estiver ausente.
"""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Ambiente de execução ("development" | "production"). Usado só para
    # ativar checagens de segurança que não fazem sentido travar em dev
    # (ex.: exigir SECRET_KEY forte, exigir HTTPS).
    ENVIRONMENT: str = "development"

    # Banco de dados
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce_ml"

    @field_validator("DATABASE_URL")
    @classmethod
    def _force_asyncpg_driver(cls, value: str) -> str:
        """Normaliza a URL para o driver assíncrono (asyncpg).

        Provedores de deploy (Railway, Heroku etc.) injetam a variável
        DATABASE_URL no formato "postgres://..." ou "postgresql://...",
        sem o sufixo "+asyncpg" que o SQLAlchemy async exige. Sem essa
        normalização, o boot em produção falhava com "the loaded 'psycopg2'
        is not async" só por causa do formato da URL gerada pelo provedor.
        """
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    # Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    ML_PREDICTION_CACHE_TTL: int = 3600  # segundos

    # Autenticação (JWT)
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Bloqueio de conta após tentativas de login malsucedidas (força bruta).
    # Contado por CONTA (e-mail), não por IP+conta — um atacante trocando de
    # IP não reseta o contador. Ver app/api/v1/endpoints/auth.py::login.
    AUTH_MAX_FAILED_ATTEMPTS: int = 5
    AUTH_LOCKOUT_SECONDS: int = 900

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Armazenamento de imagens de produto. "local" grava em disco no próprio
    # back-end (MEDIA_ROOT) e serve via StaticFiles em MEDIA_BASE_URL — é o
    # suficiente para o TCC/demo. Trocar para um provedor de nuvem (S3 etc.)
    # no deploy futuro é implementar um novo StorageBackend em
    # app/core/storage.py e mudar STORAGE_BACKEND; nenhum outro código
    # (models, endpoints, front-end) depende de como/onde o arquivo é salvo,
    # só da URL final devolvida pela API.
    STORAGE_BACKEND: str = "local"
    MEDIA_ROOT: str = "static/uploads"
    MEDIA_BASE_URL: str = "/media"
    MAX_UPLOAD_SIZE_MB: int = 5

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

    # Frete (Melhor Envio). CEP fixo de origem = centro de distribuição da
    # loja. Sem token configurado, o endpoint de cotação responde com erro
    # claro em vez de uma exceção genérica do httpx.
    MELHOR_ENVIO_TOKEN: str | None = None
    MELHOR_ENVIO_BASE_URL: str = "https://sandbox.melhorenvio.com.br"
    MELHOR_ENVIO_CEP_ORIGEM: str = "01310-100"

    # Pagamento (Mercado Pago). ACCESS_TOKEN é secreto (só back-end);
    # PUBLIC_KEY é exposta ao front de propósito (é assim que o SDK de
    # tokenização funciona — não é um segredo). WEBHOOK_SECRET valida a
    # assinatura HMAC de cada notificação recebida.
    MERCADO_PAGO_ACCESS_TOKEN: str | None = None
    MERCADO_PAGO_PUBLIC_KEY: str | None = None
    MERCADO_PAGO_WEBHOOK_SECRET: str | None = None
    MERCADO_PAGO_BASE_URL: str = "https://api.mercadopago.com"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def assert_production_safety(self) -> None:
        """Chamado no startup da aplicação (ver app/main.py).

        Evita o erro clássico de subir em produção com a SECRET_KEY padrão
        do repositório — quem descobrisse isso conseguiria forjar tokens JWT
        de qualquer usuário/role. Só é exigido quando ENVIRONMENT=production;
        em dev/local o valor padrão continua funcionando sem fricção.
        """
        if self.ENVIRONMENT == "production" and self.SECRET_KEY == "change-me":
            raise RuntimeError(
                "SECRET_KEY continua com o valor padrão em ambiente de produção. "
                "Defina uma chave aleatória forte na variável de ambiente SECRET_KEY antes de subir."
            )


@lru_cache
def get_settings() -> Settings:
    """Cache simples em processo: evita reler/reparsear o .env a cada request."""
    return Settings()


settings = get_settings()
