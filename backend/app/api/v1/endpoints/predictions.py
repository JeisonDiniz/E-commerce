"""
Endpoints de predição de ML.

Estratégia de cache (Redis): a leitura de previsões é bem mais frequente
(dashboard, catálogo) do que a geração de novas previsões (que só ocorre
quando um novo treinamento roda — ver módulo de ML na Etapa 3). Por isso,
cada consulta primeiro tenta o Redis; só recorre ao Postgres em cache miss,
e então repopula o cache. As chaves seguem o padrão
`prediction:{model_type}:{alvo}` com TTL configurável via
`ML_PREDICTION_CACHE_TTL`.

Este router já está pronto para servir predições reais assim que o
pipeline de treinamento (Etapa 3) passar a gravar em `ml_predictions`.
"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.models.enums import ModelType, SuggestionStatus, UserRole
from app.models.ml import MLPrediction, MLModelMetric, RestockSuggestion
from app.schemas.ml import (
    MLModelMetricRead,
    MLPredictionRead,
    RestockSuggestionRead,
    RestockSuggestionReview,
)
from app.models.user import User

router = APIRouter(tags=["Machine Learning"])

_STAFF_ROLES = (UserRole.staff, UserRole.manager, UserRole.admin)


async def _cached_predictions(
    redis: Redis, db: AsyncSession, cache_key: str, stmt
) -> list[MLPredictionRead]:
    cached = await redis.get(cache_key)
    if cached is not None:
        return [MLPredictionRead.model_validate_json(item) for item in json.loads(cached)]

    result = await db.execute(stmt)
    predictions = [MLPredictionRead.model_validate(p) for p in result.scalars().all()]

    if predictions:
        payload = [p.model_dump_json() for p in predictions]
        await redis.set(cache_key, json.dumps(payload), ex=settings.ML_PREDICTION_CACHE_TTL)

    return predictions


@router.get("/predictions/variants/{variant_id}", response_model=list[MLPredictionRead])
async def get_variant_predictions(
    variant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> list[MLPredictionRead]:
    """Previsão de demanda (Random Forest) para uma variante específica."""
    stmt = (
        select(MLPrediction)
        .where(MLPrediction.variant_id == variant_id, MLPrediction.model_type == ModelType.random_forest)
        .order_by(MLPrediction.prediction_date)
    )
    return await _cached_predictions(redis, db, f"prediction:random_forest:{variant_id}", stmt)


@router.get("/predictions/categories/{category_id}", response_model=list[MLPredictionRead])
async def get_category_predictions(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> list[MLPredictionRead]:
    """Série temporal (Prophet) de sazonalidade/tendência para uma categoria."""
    stmt = (
        select(MLPrediction)
        .where(MLPrediction.category_id == category_id, MLPrediction.model_type == ModelType.prophet)
        .order_by(MLPrediction.prediction_date)
    )
    return await _cached_predictions(redis, db, f"prediction:prophet:{category_id}", stmt)


@router.get("/ml/metrics", response_model=list[MLModelMetricRead], dependencies=[Depends(require_roles(*_STAFF_ROLES))])
async def get_model_metrics(db: AsyncSession = Depends(get_db)) -> list[MLModelMetric]:
    """Histórico de métricas (MAE/MAPE/RMSE) de cada treinamento — evidência para a defesa do TCC."""
    stmt = select(MLModelMetric).order_by(MLModelMetric.trained_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get(
    "/restock-suggestions",
    response_model=list[RestockSuggestionRead],
    dependencies=[Depends(require_roles(*_STAFF_ROLES))],
)
async def list_restock_suggestions(
    suggestion_status: SuggestionStatus | None = None, db: AsyncSession = Depends(get_db)
) -> list[RestockSuggestion]:
    stmt = select(RestockSuggestion).order_by(RestockSuggestion.created_at.desc())
    if suggestion_status is not None:
        stmt = stmt.where(RestockSuggestion.status == suggestion_status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post(
    "/restock-suggestions/{suggestion_id}/review",
    response_model=RestockSuggestionRead,
    dependencies=[Depends(require_roles(*_STAFF_ROLES))],
)
async def review_restock_suggestion(
    suggestion_id: uuid.UUID,
    payload: RestockSuggestionReview,
    current_user: User = Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> RestockSuggestion:
    """
    Aprova ou rejeita uma sugestão de reposição gerada pelo ML.
    Nunca dispara compra/entrada de estoque automaticamente — apenas
    registra a decisão humana. A entrada efetiva no estoque, quando a
    mercadoria chega, é lançada manualmente via POST /inventory/movements.
    """
    suggestion = await db.get(RestockSuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sugestão não encontrada")
    if suggestion.status != SuggestionStatus.pendente:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta sugestão já foi revisada")

    suggestion.status = SuggestionStatus.aprovada if payload.approve else SuggestionStatus.rejeitada
    suggestion.reviewed_by = current_user.id
    suggestion.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(suggestion)
    return suggestion