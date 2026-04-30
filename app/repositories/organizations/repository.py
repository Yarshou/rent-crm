from uuid import UUID

from db.models import Organization
from repositories import BaseRepository
from sqlalchemy import select

__all__ = ["OrganizationRepository"]


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

    async def get_by_name(self, name: str) -> Organization | None:
        result = await self.session.execute(select(Organization).where(Organization.name == name))
        return result.scalar_one_or_none()

    async def list_by_ids(self, organization_ids: list[UUID]) -> list[Organization]:
        if not organization_ids:
            return []

        result = await self.session.execute(
            select(Organization).where(Organization.id.in_(organization_ids)).order_by(Organization.name),
        )
        return list(result.scalars().all())
