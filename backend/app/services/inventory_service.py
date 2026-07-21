"""
Regra de negócio de estoque: toda alteração de saldo passa por aqui, para
garantir que `inventory.quantity` (snapshot) e `inventory_movements` (log)
nunca fiquem dessincronizados.
"""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MovementType
from app.models.inventory import Inventory, InventoryMovement

# Movimentos que aumentam o saldo em estoque.
_INCREASE = {MovementType.entrada, MovementType.devolucao}
# Movimentos que diminuem o saldo em estoque.
_DECREASE = {MovementType.saida}
# 'ajuste' é tratado como correção absoluta (ex: inventário físico divergente).


async def apply_movement(
    db: AsyncSession,
    variant_id: uuid.UUID,
    movement_type: MovementType,
    quantity: int,
    reason: str | None,
    reference_order_id: uuid.UUID | None,
    created_by: uuid.UUID | None,
) -> InventoryMovement:
    result = await db.execute(select(Inventory).where(Inventory.variant_id == variant_id).with_for_update())
    inventory = result.scalar_one_or_none()
    if inventory is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Estoque não encontrado para esta variante")

    if movement_type in _DECREASE:
        if inventory.quantity < quantity:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Saldo insuficiente em estoque")
        inventory.quantity -= quantity
    elif movement_type in _INCREASE:
        inventory.quantity += quantity
    elif movement_type == MovementType.ajuste:
        inventory.quantity = quantity

    movement = InventoryMovement(
        variant_id=variant_id,
        movement_type=movement_type,
        quantity=quantity,
        reason=reason,
        reference_order_id=reference_order_id,
        created_by=created_by,
    )
    db.add(movement)
    await db.flush()
    return movement