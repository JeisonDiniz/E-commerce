"""
Conexão assíncrona com o PostgreSQL via SQLAlchemy 2.0.

Por quê assíncrono? A API precisa lidar bem com I/O concorrente típico de
e-commerce (múltiplos usuários navegando o catálogo, carrinho e checkout ao
mesmo tempo) sem bloquear o event loop do FastAPI — é um dos requisitos
explícitos do projeto ("execução assíncrona nativa").
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,        # mude para True durante debug para ver o SQL gerado
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # detecta conexões mortas antes de usá-las
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Dependency do FastAPI: uma sessão por request, fechada ao final."""
    async with AsyncSessionLocal() as session:
        yield session
