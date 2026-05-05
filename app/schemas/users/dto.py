from datetime import datetime
from uuid import UUID

from db.models import OrganizationRole
from schemas.base import ImmutableDTO

__all__ = ["OrganizationMemberDTO", "UserDTO"]


class UserDTO(ImmutableDTO):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    email: str
    full_name: str
    is_super_admin: bool
    password_hash: str


class OrganizationMemberDTO(ImmutableDTO):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    organization_id: UUID
    user_id: UUID
    role: OrganizationRole
