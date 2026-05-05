from datetime import datetime
from uuid import UUID

from schemas.base import ImmutableDTO

__all__ = ["OrganizationDTO"]


class OrganizationDTO(ImmutableDTO):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    name: str
