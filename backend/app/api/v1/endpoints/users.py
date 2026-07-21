from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import Address, User
from app.schemas.user import AddressCreate, AddressRead, UserRead

router = APIRouter(prefix="/users", tags=["Usuários"])


@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/me/addresses", response_model=list[AddressRead])
async def list_addresses(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[Address]:
    result = await db.execute(select(Address).where(Address.user_id == current_user.id))
    return list(result.scalars().all())


@router.post("/me/addresses", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
async def add_address(
    payload: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Address:
    address = Address(user_id=current_user.id, **payload.model_dump())
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address