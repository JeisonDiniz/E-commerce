"""
Cotação de frete via Melhor Envio.

Isolado em service (em vez de ficar direto no endpoint) porque a mesma
lógica de "somar peso/dimensões das variantes do carrinho" será reutilizada
quando o checkout precisar reconferir o frete antes de criar o pedido.
"""
import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.catalog import ProductVariant
from app.schemas.shipping import ShippingItemInput, ShippingOption


async def quote_shipping(
    db: AsyncSession, cep_destino: str, items: list[ShippingItemInput]
) -> list[ShippingOption]:
    if not settings.MELHOR_ENVIO_TOKEN:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Cálculo de frete indisponível: MELHOR_ENVIO_TOKEN não configurado.",
        )

    variant_ids = [item.variant_id for item in items]
    quantity_by_id = {item.variant_id: item.quantity for item in items}
    result = await db.execute(select(ProductVariant).where(ProductVariant.id.in_(variant_ids)))
    variants = {v.id: v for v in result.scalars().all()}

    total_weight_grams = 0
    max_height_cm = 0.0
    max_width_cm = 0.0
    total_length_cm = 0.0
    for variant_id, quantity in quantity_by_id.items():
        variant = variants.get(variant_id)
        if variant is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Variante {variant_id} não encontrada")
        total_weight_grams += variant.weight_grams * quantity
        max_height_cm = max(max_height_cm, float(variant.height_cm))
        max_width_cm = max(max_width_cm, float(variant.width_cm))
        # Simplificação: empilha o comprimento por unidade. Empacotamento
        # ótimo (bin packing) fica fora do escopo do TCC.
        total_length_cm += float(variant.length_cm) * quantity

    async with httpx.AsyncClient(base_url=settings.MELHOR_ENVIO_BASE_URL, timeout=10) as client:
        response = await client.post(
            "/api/v2/me/shipment/calculate",
            headers={
                "Authorization": f"Bearer {settings.MELHOR_ENVIO_TOKEN}",
                "User-Agent": "Loja Virtual TCC (contato@loja.com)",
            },
            json={
                "from": {"postal_code": settings.MELHOR_ENVIO_CEP_ORIGEM},
                "to": {"postal_code": cep_destino},
                "package": {
                    "weight": round(total_weight_grams / 1000, 3),  # kg
                    "height": max_height_cm,
                    "width": max_width_cm,
                    "length": total_length_cm,
                },
            },
        )

    if response.status_code >= 400:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"Melhor Envio recusou a cotação: {response.text[:300]}"
        )

    data = response.json()
    return [
        ShippingOption(service=item["name"], price=float(item["price"]), deadline_days=item["delivery_time"])
        for item in data
        if "error" not in item
    ]
