from __future__ import annotations

from pydantic import BaseModel, EmailStr


class RoleOut(BaseModel):
    id: str
    name: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    assigned_vehicle_id: str | None = None
    roles: list[RoleOut]

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CreateUserIn(BaseModel):
    email: EmailStr
    password: str

