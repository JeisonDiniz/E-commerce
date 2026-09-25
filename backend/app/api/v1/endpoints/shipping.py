from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.shipping import ShippingQuoteRequest, ShippingQuoteResponse
from app.services.shipping_service import quote_shipping

router = APIRouter(prefix="/shipping", tags=["Frete"])


@router.post("/quote", response_model=ShippingQuoteResponse)
async def quote(payload: ShippingQuoteRequest, db: AsyncSession = Depends(get_db)) -> ShippingQuoteResponse:
    options = await quote_shipping(db, payload.cep_destino, payload.items)
    return ShippingQuoteResponse(options=options)
