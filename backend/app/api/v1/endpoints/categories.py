from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.catalog import Category
from app.models.enums import UserRole
from app.schemas.catalog import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["Categorias"])


@router.get("", response_model=list[CategoryRead])
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[Category]:
    result = await db.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.manager, UserRole.admin))],
)
async def create_category(payload: CategoryCreate, db: AsyncSession = Depends(get_db)) -> Category:
    category = Category(**payload.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category