import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.commerce import Order
from app.models.enums import OrderStatus, UserRole
from app.models.user import User
from app.schemas.commerce import OrderCreate, OrderRead
from app.services.order_service import checkout

router = APIRouter(prefix="/orders", tags=["Pedidos"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Order:
    return await checkout(
        db,
        user_id=current_user.id,
        shipping_address_id=payload.shipping_address_id,
        payment_method=payload.payment_method,
    )


@router.get("/me", response_model=list[OrderRead])
async def list_my_orders(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[Order]:
    stmt = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


@router.get(
    "",
    response_model=list[OrderRead],
    dependencies=[Depends(require_roles(UserRole.staff, UserRole.manager, UserRole.admin))],
)
async def list_all_orders(db: AsyncSession = Depends(get_db)) -> list[Order]:
    stmt = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    dependencies=[Depends(require_roles(UserRole.staff, UserRole.manager, UserRole.admin))],
)
async def update_order_status(order_id: uuid.UUID, new_status: OrderStatus, db: AsyncSession = Depends(get_db)) -> Order:
    stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido não encontrado")

    order.status = new_status
    await db.commit()
    await db.refresh(order)
    return order