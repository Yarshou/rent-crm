from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator
from schemas.base import EmailStr, PasswordStr

__all__ = [
    "AuthResponse",
    "CurrentUserResponse",
    "LoginRequest",
    "OrganizationContextResponse",
    "RegisterUserRequest",
    "TokenPayload",
    "TokenResponse",
]


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: PasswordStr = Field(min_length=8, max_length=64)
    confirm_password: PasswordStr = Field(min_length=8, max_length=64)
    full_name: str = Field(min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=64)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(TokenResponse):
    pass


class OrganizationContextResponse(BaseModel):
    id: UUID
    name: str


class CurrentUserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    is_super_admin: bool
    organization: OrganizationContextResponse


class TokenPayload(BaseModel):
    sub: str
    role: str
    type: str = "access"
    exp: int
