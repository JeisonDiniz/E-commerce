import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.storage import storage
from app.models.catalog import Product, ProductImage, ProductVariant
from app.models.commerce import Cart, CartItem
from app.models.user import User
from app.schemas.commerce import CartItemRead, CartItemCreate, CartItemUpdate, CartRead

router = APIRouter(prefix="/cart", tags=["Carrinho"])


async def _get_or_create_cart(db: AsyncSession, user_id: uuid.UUID) -> Cart:
    stmt = select(Cart).where(Cart.user_id == user_id).options(selectinload(Cart.items))
    result = await db.execute(stmt)
    cart = result.scalar_one_or_none()
    if cart is None:
        # BUG real encontrado e corrigido aqui: a suposição antiga era que um
        # `Cart` recém-criado já nasce com `.items` = [] em memória, sem
        # precisar de nada mais. Não é o que acontece na prática — depois do
        # `flush()`, o objeto vira "persistente" e o SQLAlchemy passa a
        # tratar `.items` como não carregado, disparando um lazy-load só na
        # primeira leitura (ex.: `add_item` faz `for i in cart.items` logo
        # em seguida). Como esse lazy-load é síncrono por baixo dos panos,
        # ele quebra com "MissingGreenlet" fora do contexto do SQLAlchemy
        # async — ou seja, o PRIMEIRO "adicionar ao carrinho" de QUALQUER
        # cliente novo (o carrinho dele ainda não existe) sempre dava 500.
        # `db.refresh(..., attribute_names=["items"])` força um reload de
        # verdade, via `await`, dentro do contexto async correto.
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.flush()
        await db.refresh(cart, attribute_names=["items"])
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

        image_url = None
        if variant is not None:
            # Prioriza uma foto da MESMA cor da variante no carrinho; sem
            # nenhuma daquela cor, cai pra foto "geral" (color IS NULL) e só
            # por último qualquer foto de outra cor — mesma lógica de
            # fallback da galeria em ProductDetailPage, resolvida aqui no
            # back-end (o carrinho não carrega o produto inteiro).
            #
            # Precisa ser um CASE explícito, não `(color == variant.color)`
            # direto: em SQL, comparar uma coluna NULL com qualquer valor dá
            # NULL (não FALSE), e o Postgres ordena NULL antes de qualquer
            # valor em ORDER BY ... DESC por padrão — na prática, a foto
            # "geral" (color NULL) sempre vencia a foto da cor certa, o
            # oposto da prioridade pretendida. Testado e confirmado via API
            # antes dessa correção.
            color_rank = case(
                (ProductImage.color == variant.color, 2),
                (ProductImage.color.is_(None), 1),
                else_=0,
            )
            image_stmt = (
                select(ProductImage)
                .where(ProductImage.product_id == variant.product_id)
                .order_by(color_rank.desc(), ProductImage.is_primary.desc(), ProductImage.sort_order.asc())
                .limit(1)
            )
            image_result = await db.execute(image_stmt)
            image = image_result.scalars().first()
            if image is not None:
                image_url = storage.url_for(image.storage_key)

        items.append(
            CartItemRead(
                id=item.id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                sku=variant.sku if variant else None,
                product_name=product_name,
                unit_price=variant.price if variant else None,
                image_url=image_url,
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
    # `attribute_names=["items"]` (não um refresh "cru"): sem isso, o
    # refresh expira a relação `.items` sem recarregá-la, e o acesso logo
    # abaixo em `_to_cart_read` dispara o mesmo lazy-load síncrono que
    # quebra com "MissingGreenlet" (ver comentário em _get_or_create_cart).
    await db.refresh(cart, attribute_names=["items"])
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
    await db.refresh(cart, attribute_names=["items"])
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