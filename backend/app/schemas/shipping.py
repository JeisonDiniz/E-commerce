import uuid

from pydantic import BaseModel, Field


class ShippingItemInput(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(gt=0)


class ShippingQuoteRequest(BaseModel):
    cep_destino: str = Field(min_length=8, max_length=9)
    items: list[ShippingItemInput] = Field(min_length=1)


class ShippingOption(BaseModel):
    service: str
    price: float
    deadline_days: int


class ShippingQuoteResponse(BaseModel):
    options: list[ShippingOption]
