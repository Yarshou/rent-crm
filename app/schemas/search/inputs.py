from uuid import UUID

from schemas.base import MutableDTO

__all__ = ["SearchInput"]


class SearchInput(MutableDTO):
    organization_id: UUID
    q: str
    limit: int = 10
