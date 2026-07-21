import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.catalog import Product, ProductVariant
from app.models.enums import UserRole
from app.models.inventory import Inventory
from app.models.user import User
from app.schemas.inventory import InventoryMovementCreate, InventoryMovementRead, InventoryRead, LowStockItem
from app.services.inventory_service import apply_movement

router = APIRouter(prefix="/inventory", tags=["Estoque"])

_STAFF_ROLES = (UserRole.staff, UserRole.manager, UserRole.admin)


@router.get("/low-stock", response_model=list[LowStockItem], dependencies=[Depends(require_roles(*_STAFF_ROLES))])
async def low_stock(db: AsyncSession = Depends(get_db)) -> list[LowStockItem]:
    """Itens em risco de ruptura — quantidade em estoque abaixo do mínimo definido."""
    stmt = (
        select(Inventory, ProductVariant, Product)
        .join(ProductVariant, ProductVariant.id == Inventory.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .where(Inventory.quantity <= Inventory.min_quantity)
    )
    result = await db.execute(stmt)
    return [
        LowStockItem(
            variant_id=variant.id,
            sku=variant.sku,
            product_name=product.name,
            quantity=inv.quantity,
            min_quantity=inv.min_quantity,
        )
        for inv, variant, product in result.all()
    ]


@router.get("/{variant_id}", response_model=InventoryRead, dependencies=[Depends(require_roles(*_STAFF_ROLES))])
async def get_inventory(variant_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Inventory:
    result = await db.execute(select(Inventory).where(Inventory.variant_id == variant_id))
    inventory = result.scalar_one_or_none()
    if inventory is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Estoque não encontrado para esta variante")
    return inventory


@router.post(
    "/movements",
    response_model=InventoryMovementRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*_STAFF_ROLES))],
)
async def create_movement(
    payload: InventoryMovementCreate,
    current_user: User = Depends(require_roles(*_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    movement = await apply_movement(
        db,
        variant_id=payload.variant_id,
        movement_type=payload.movement_type,
        quantity=payload.quantity,
        reason=payload.reason,
        reference_order_id=payload.reference_order_id,
        created_by=current_user.id,
    )
    await db.commit()
    await db.refresh(movement)
    return movement