import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MovementType


class InventoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    min_quantity: int
    max_quantity: int
    updated_at: datetime


class InventoryMovementCreate(BaseModel):
    variant_id: uuid.UUID
    movement_type: MovementType
    quantity: int = Field(gt=0)
    reason: str | None = None
    reference_order_id: uuid.UUID | None = None


class InventoryMovementRead(InventoryMovementCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_by: uuid.UUID | None
    created_at: datetime


class LowStockItem(BaseModel):
    """Usado no dashboard para alertar sobre risco de ruptura de estoque."""

    variant_id: uuid.UUID
    sku: str
    product_name: str
    quantity: int
    min_quantity: int
