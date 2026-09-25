import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ModelType, SuggestionStatus


class MLPredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    model_type: ModelType
    variant_id: uuid.UUID | None
    category_id: uuid.UUID | None
    prediction_date: date
    predicted_quantity: float
    confidence_lower: float | None
    confidence_upper: float | None
    model_version: str
    generated_at: datetime


class MLModelMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    model_type: ModelType
    model_version: str
    mae: float
    mape: float
    rmse: float | None
    training_samples: int
    trained_at: datetime
    notes: str | None


class RestockSuggestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    variant_id: uuid.UUID
    based_on_prediction_id: uuid.UUID | None
    suggested_quantity: int
    status: SuggestionStatus
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class RestockSuggestionReview(BaseModel):
    """Payload usado pelo gestor para aprovar ou rejeitar uma sugestão — nunca há aprovação automática."""

    approve: bool