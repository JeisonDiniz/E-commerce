import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.catalog import Product, ProductVariant
from app.models.commerce import Cart, CartItem
from app.models.user import User
from app.schemas.commerce import CartItemRead, CartItemCreate, CartItemUpdate, CartRead

router = APIRouter(prefix="/cart", tags=["Carrinho"])


async def _get_or_create_cart(db: AsyncSession, user_id: uuid.UUID) -> Cart:
    stmt = select(Cart).where(Cart.user_id == user_id).options(selectinload(Cart.items))
    result = await db.execute(stmt)
    cart = result.scalar_one_or_none()
    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.flush()
        cart.items = []
    return cart


async def _to_cart_read(db: AsyncSession, cart: Cart) -> CartRead:
    """Enriquece cada item do carrinho com SKU/nome/preço da variante para exibição."""
    items: list[CartItemRead] = []
    for item in cart.items:
        stmt = (
            select(ProductVariant, Product.name)
            .join(Product, Product.id == ProductVariant.product_id)
            .where(ProductVariant.id == item.variant_id)
        )
        result = await db.execute(stmt)
        row = result.first()
        variant, product_name = row if row else (None, None)
        items.append(
            CartItemRead(
                id=item.id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                sku=variant.sku if variant else None,
                product_name=product_name,
                unit_price=variant.price if variant else None,
            )
        )
    return CartRead(id=cart.id, user_id=cart.user_id, items=items)


@router.get("", response_model=CartRead)
async def get_cart(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> CartRead:
    cart = await _get_or_create_cart(db, current_user.id)
    await db.commit()
    return await _to_cart_read(db, cart)


@router.post("/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
async def add_item(
    payload: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartRead:
    cart = await _get_or_create_cart(db, current_user.id)

    existing_item = next((i for i in cart.items if i.variant_id == payload.variant_id), None)
    if existing_item is not None:
        existing_item.quantity += payload.quantity
    else:
        cart.items.append(CartItem(variant_id=payload.variant_id, quantity=payload.quantity))

    await db.commit()
    await db.refresh(cart)
    return await _to_cart_read(db, cart)


@router.patch("/items/{item_id}", response_model=CartRead)
async def update_item(
    item_id: uuid.UUID,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartRead:
    cart = await _get_or_create_cart(db, current_user.id)
    item = next((i for i in cart.items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item não encontrado no carrinho")

    item.quantity = payload.quantity
    await db.commit()
    await db.refresh(cart)
    return await _to_cart_read(db, cart)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    cart = await _get_or_create_cart(db, current_user.id)
    item = next((i for i in cart.items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item não encontrado no carrinho")
    await db.delete(item)
    await db.commit()