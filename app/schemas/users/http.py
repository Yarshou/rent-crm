from uuid import UUID

from db.models import OrganizationRole
from pydantic import BaseModel, Field
from schemas.base.common import BaseEntityResponse
from schemas.organizations.http import OrganizationResponse

__all__ = [
    "OrganizationMemberCreateRequest",
    "OrganizationMemberResponse",
    "UserCreateRequest",
    "UserOrganizationsResponse",
    "UserPasswordUpdateRequest",
    "UserProfileUpdateRequest",
    "UserResponse",
]


class UserCreateRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password_hash: str = Field(min_length=1, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    is_super_admin: bool = False


class UserProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)


class UserPasswordUpdateRequest(BaseModel):
    password_hash: str = Field(min_length=1, max_length=255)


class OrganizationMemberCreateRequest(BaseModel):
    organization_id: UUID
    role: OrganizationRole = OrganizationRole.owner


class UserResponse(BaseEntityResponse):
    email: str
    full_name: str
    is_super_admin: bool


class OrganizationMemberResponse(BaseEntityResponse):
    organization_id: UUID
    user_id: UUID
    role: OrganizationRole


class UserOrganizationsResponse(BaseModel):
    organizations: list[OrganizationResponse]
