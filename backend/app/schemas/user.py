import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import UserRole


class UserCreate(BaseModel):
    """Payload do cadastro público (POST /auth/register).

    Propositalmente SEM campo `role`: quem se cadastra pela API é sempre
    `customer` (ver app/api/v1/endpoints/auth.py::register). Contas
    staff/manager/admin só são criadas via backend/scripts/seed_database.py
    ou diretamente no banco — nunca por um endpoint público, para que
    ninguém consiga se auto-promover a administrador.
    """

    name: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime


class AddressCreate(BaseModel):
    street: str
    number: str
    complement: str | None = None
    neighborhood: str
    city: str
    state: str
    zip_code: str
    is_default: bool = False


class AddressRead(AddressCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
