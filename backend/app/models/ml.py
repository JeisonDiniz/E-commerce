import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPKMixin
from app.models.enums import ModelType, SuggestionStatus, pg_enum


class MLPrediction(UUIDPKMixin, Base):
    """
    Previsão gerada por um dos dois modelos.
    Random Forest prevê por variante (variant_id); Prophet prevê por
    categoria/agregado temporal (category_id). Persistida aqui para
    auditoria histórica; espelhada no Redis para leitura rápida do dashboard.
    """

    __tablename__ = "ml_predictions"
    __table_args__ = (
        CheckConstraint(
            "(model_type = 'random_forest' AND variant_id IS NOT NULL AND category_id IS NULL) OR "
            "(model_type = 'prophet' AND category_id IS NOT NULL AND variant_id IS NULL)",
            name="ck_prediction_target_matches_model",
        ),
    )

    model_type: Mapped[ModelType] = mapped_column(pg_enum(ModelType, "model_type"), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=True
    )
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    confidence_lower: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    confidence_upper: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MLModelMetric(UUIDPKMixin, Base):
    """Métricas de avaliação de cada treinamento (MAE/MAPE/RMSE) — valida os critérios de aceitação do TCC."""

    __tablename__ = "ml_model_metrics"

    model_type: Mapped[ModelType] = mapped_column(pg_enum(ModelType, "model_type"), nullable=False)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    mae: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    mape: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    rmse: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    training_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class RestockSuggestion(UUIDPKMixin, Base):
    """
    Sugestão de reposição derivada de uma previsão. Nasce sempre 'pendente':
    a decisão de compra é sempre humana (requisito central do projeto —
    ML sugere, o gestor aprova ou rejeita).
    """

    __tablename__ = "restock_suggestions"

    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False
    )
    based_on_prediction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ml_predictions.id", ondelete="SET NULL"), nullable=True
    )
    suggested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SuggestionStatus] = mapped_column(
        pg_enum(SuggestionStatus, "suggestion_status"), nullable=False, default=SuggestionStatus.pendente
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    variant: Mapped["ProductVariant"] = relationship()