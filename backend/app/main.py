"""
Ponto de entrada da API FastAPI.

Documentação automática (Swagger em /docs, ReDoc em /redoc) é gerada
nativamente pelo FastAPI a partir dos schemas Pydantic e das assinaturas
dos endpoints — atende ao requisito de "documentação automática da API".
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.redis_client import redis_client
from app.core.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.assert_production_safety()
    yield
    await redis_client.aclose()


app = FastAPI(
    title="Loja Virtual de Roupas — Estoque Inteligente e ML",
    description=(
        "API para e-commerce de moda com controle de estoque e predição de "
        "tendências de venda via Machine Learning (Prophet + Random Forest)."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix="/api/v1")

if settings.STORAGE_BACKEND == "local":
    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)
    app.mount(settings.MEDIA_BASE_URL, StaticFiles(directory=media_root), name="media")


@app.get("/health", tags=["Infraestrutura"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


# Front-end (build de produção do Vite), servido pelo próprio back-end.
#
# Deploy em um único serviço (ver Dockerfile na raiz do repo, que builda o
# React e copia o resultado para frontend_dist/) evita CORS e o problema de
# URLs relativas (ex.: "/media/foto.jpg", "/api/v1/...") resolverem contra o
# domínio errado quando front e back estão em domínios separados. Em
# desenvolvimento (`uvicorn --reload` sem esse diretório) isso não é
# registrado — nada muda no fluxo local com `npm run dev` na porta 5173.
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend_dist"
if _FRONTEND_DIST.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=_FRONTEND_DIST / "assets"),
        name="frontend-assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str) -> FileResponse:
        """Fallback estilo SPA: qualquer rota que não seja de API/mídia (ex.:
        "/admin/produtos") deve devolver o index.html do React Router, não
        um 404 — o roteamento dessas rotas é feito no cliente."""
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_FRONTEND_DIST / "index.html")