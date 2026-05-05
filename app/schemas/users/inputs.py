from uuid import UUID

from db.models import OrganizationRole
from schemas.base import MutableDTO

__all__ = [
    "OrganizationAccessInput",
    "OrganizationMembershipCreateInput",
    "UserAuthenticateInput",
    "UserByEmailInput",
    "UserCreateInput",
    "UserGetInput",
    "UserListMembershipsInput",
    "UserListOrganizationsInput",
    "UserPasswordUpdateInput",
    "UserProfileUpdateInput",
    "UserRegisterInput",
]


class UserGetInput(MutableDTO):
    user_id: UUID


class UserByEmailInput(MutableDTO):
    email: str


class UserCreateInput(MutableDTO):
    email: str
    password_hash: str
    full_name: str
    is_super_admin: bool = False


class UserRegisterInput(MutableDTO):
    email: str
    password: str
    full_name: str


class UserAuthenticateInput(MutableDTO):
    email: str
    password: str


class UserProfileUpdateInput(MutableDTO):
    user_id: UUID
    full_name: str


class UserPasswordUpdateInput(MutableDTO):
    user_id: UUID
    password_hash: str


class OrganizationMembershipCreateInput(MutableDTO):
    user_id: UUID
    organization_id: UUID
    role: OrganizationRole = OrganizationRole.owner


class UserListMembershipsInput(MutableDTO):
    user_id: UUID


class UserListOrganizationsInput(MutableDTO):
    user_id: UUID
    offset: int = 0
    limit: int | None = None


class OrganizationAccessInput(MutableDTO):
    user_id: UUID
    organization_id: UUID
