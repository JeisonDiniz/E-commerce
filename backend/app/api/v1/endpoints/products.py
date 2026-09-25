import io
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.storage import storage
from app.models.catalog import Product, ProductImage, ProductVariant
from app.models.enums import GenderType, SeasonType, UserRole
from app.models.inventory import Inventory
from app.schemas.catalog import (
    ProductCreate,
    ProductImageRead,
    ProductRead,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantRead,
)

router = APIRouter(prefix="/products", tags=["Catálogo"])

# Formatos aceitos para upload de imagem de produto: extensão de saída fixa
# por formato (nunca a extensão enviada pelo cliente) e limite de pixels
# para evitar "decompression bomb" (imagem pequena em bytes que decodifica
# em um bitmap gigante e esgota memória do servidor).
_ALLOWED_IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
Image.MAX_IMAGE_PIXELS = 40_000_000  # ~40MP — protege contra "decompression bomb"


def _variant_to_read(variant: ProductVariant) -> ProductVariantRead:
    data = ProductVariantRead.model_validate(variant)
    data.stock_quantity = variant.inventory.quantity if variant.inventory else None
    return data


def _image_to_read(image: ProductImage) -> ProductImageRead:
    data = ProductImageRead.model_validate(image)
    data.url = storage.url_for(image.storage_key)
    return data


def _product_to_read(product: Product) -> ProductRead:
    read = ProductRead.model_validate(product)
    read.variants = [_variant_to_read(v) for v in product.variants]
    read.images = [_image_to_read(i) for i in product.images]
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
        selectinload(Product.variants).selectinload(ProductVariant.inventory),
        selectinload(Product.images),
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
        .options(
            selectinload(Product.variants).selectinload(ProductVariant.inventory),
            selectinload(Product.images),
        )
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
        .options(
            selectinload(Product.variants).selectinload(ProductVariant.inventory),
            selectinload(Product.images),
        )
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
        .options(
            selectinload(Product.variants).selectinload(ProductVariant.inventory),
            selectinload(Product.images),
        )
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


@router.post(
    "/{product_id}/images",
    response_model=ProductImageRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.manager, UserRole.admin))],
)
async def upload_product_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    color: str | None = Form(None),
    is_primary: bool = Form(False),
    db: AsyncSession = Depends(get_db),
) -> ProductImageRead:
    """Upload de uma foto do produto, opcionalmente associada a uma cor.

    A validação é propositalmente rigorosa porque este é o único endpoint da
    API que recebe um arquivo binário arbitrário de fora: content-type
    declarado é só um indício (o cliente pode mentir), então a checagem real
    é decodificar os bytes com Pillow e re-salvar a imagem — isso garante
    que o arquivo é de fato uma imagem válida (rejeita executáveis/scripts
    disfarçados com extensão de imagem) e descarta metadados/qualquer
    payload extra embutido no arquivo original.
    """
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produto não encontrado")

    if file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Formato de imagem não suportado. Envie JPG, PNG ou WEBP.",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    raw_bytes = await file.read(max_bytes + 1)
    if len(raw_bytes) > max_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Imagem maior que {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    try:
        with Image.open(io.BytesIO(raw_bytes)) as probe:
            probe.verify()
        with Image.open(io.BytesIO(raw_bytes)) as img:
            img_format = img.format
            clean_buffer = io.BytesIO()
            img.convert("RGB" if img_format == "JPEG" else img.mode).save(clean_buffer, format=img_format)
            clean_bytes = clean_buffer.getvalue()
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo enviado não é uma imagem válida.")

    extension = _ALLOWED_IMAGE_TYPES[file.content_type]
    storage_key = f"products/{product_id}/{uuid.uuid4()}.{extension}"
    storage.save(clean_bytes, storage_key)

    image = ProductImage(
        product_id=product_id,
        color=color or None,
        storage_key=storage_key,
        is_primary=is_primary,
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return _image_to_read(image)


@router.delete(
    "/{product_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.manager, UserRole.admin))],
)
async def delete_product_image(product_id: uuid.UUID, image_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    image = await db.get(ProductImage, image_id)
    if image is None or image.product_id != product_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imagem não encontrada")

    storage.delete(image.storage_key)
    await db.delete(image)
    await db.commit()