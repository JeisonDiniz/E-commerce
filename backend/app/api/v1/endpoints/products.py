import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.catalog import Product, ProductVariant
from app.models.enums import GenderType, SeasonType, UserRole
from app.models.inventory import Inventory
from app.schemas.catalog import ProductCreate, ProductRead, ProductUpdate, ProductVariantCreate, ProductVariantRead

router = APIRouter(prefix="/products", tags=["Catálogo"])


def _variant_to_read(variant: ProductVariant) -> ProductVariantRead:
    data = ProductVariantRead.model_validate(variant)
    data.stock_quantity = variant.inventory.quantity if variant.inventory else None
    return data


def _product_to_read(product: Product) -> ProductRead:
    read = ProductRead.model_validate(product)
    read.variants = [_variant_to_read(v) for v in product.variants]
    return read


@router.get("", response_model=list[ProductRead])
async def list_products(
    category_id: uuid.UUID | None = None,
    gender: GenderType | None = None,
    season: SeasonType | None = None,
    active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ProductRead]:
    stmt = select(Product).options(
        selectinload(Product.variants).selectinload(ProductVariant.inventory)
    ).where(Product.active == active)

    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if gender is not None:
        stmt = stmt.where(Product.gender == gender)
    if season is not None:
        stmt = stmt.where(Product.season == season)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().unique().all()
    return [_product_to_read(p) for p in products]


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ProductRead:
    stmt = (
        select(Product)
        .options(selectinload(Product.variants).selectinload(ProductVariant.inventory))
        .where(Product.id == product_id)
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produto não encontrado")
    return _product_to_read(product)


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.manager, UserRole.admin))],
)
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db)) -> ProductRead:
    product_data = payload.model_dump(exclude={"variants"})
    product = Product(**product_data)
    db.add(product)
    await db.flush()  # garante product.id para as variantes

    for variant_payload in payload.variants:
        variant = ProductVariant(product_id=product.id, **variant_payload.model_dump())
        db.add(variant)
        await db.flush()  # garante variant.id para o registro de estoque
        db.add(Inventory(variant_id=variant.id, quantity=0))

    await db.commit()

    stmt = (
        select(Product)
        .options(selectinload(Product.variants).selectinload(ProductVariant.inventory))
        .where(Product.id == product.id)
    )
    result = await db.execute(stmt)
    return _product_to_read(result.scalar_one())


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    dependencies=[Depends(require_roles(UserRole.manager, UserRole.admin))],
)
async def update_product(
    product_id: uuid.UUID, payload: ProductUpdate, db: AsyncSession = Depends(get_db)
) -> ProductRead:
    stmt = (
        select(Product)
        .options(selectinload(Product.variants).selectinload(ProductVariant.inventory))
        .where(Product.id == product_id)
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produto não encontrado")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return _product_to_read(product)


@router.post(
    "/{product_id}/variants",
    response_model=ProductVariantRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.manager, UserRole.admin))],
)
async def add_variant(
    product_id: uuid.UUID, payload: ProductVariantCreate, db: AsyncSession = Depends(get_db)
) -> ProductVariantRead:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produto não encontrado")

    variant = ProductVariant(product_id=product_id, **payload.model_dump())
    db.add(variant)
    await db.flush()
    inventory = Inventory(variant_id=variant.id, quantity=0)
    db.add(inventory)
    await db.commit()
    await db.refresh(variant)
    variant.inventory = inventory
    return _variant_to_read(variant)