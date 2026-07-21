"""
Ponto de entrada da API FastAPI.

Documentação automática (Swagger em /docs, ReDoc em /redoc) é gerada
nativamente pelo FastAPI a partir dos schemas Pydantic e das assinaturas
dos endpoints — atende ao requisito de "documentação automática da API".
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Infraestrutura"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}