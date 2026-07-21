"""
Cliente Redis assíncrono, compartilhado por toda a aplicação.

Uso principal (Etapa 3): cache das predições geradas pelos modelos de ML
(Prophet e Random Forest). Treinar e rodar inferência desses modelos é
custoso; como as previsões não mudam a cada requisição (só quando um novo
treinamento roda), Redis evita reprocessamento e mantém o dashboard rápido.
"""
from redis.asyncio import Redis

from app.core.config import settings

redis_client: Redis = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,  # retorna str em vez de bytes, mais simples de serializar JSON
)


async def get_redis() -> Redis:
    """Dependency do FastAPI para injetar o client Redis nos endpoints."""
    return redis_client