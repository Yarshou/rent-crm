from uuid import UUID

from db.models import Organization
from repositories import BaseRepository
from schemas.organizations import OrganizationDTO
from sqlalchemy import select

__all__ = ["OrganizationRepository"]


class OrganizationRepository(BaseRepository[Organization, OrganizationDTO]):
    model = Organization
    dto = OrganizationDTO

    async def get_by_name(self, name: str) -> OrganizationDTO | None:
        result = await self.session.execute(select(Organization).where(Organization.name == name))
        instance = result.scalar_one_or_none()
        return self._to_dto(instance) if instance is not None else None

    async def list_by_ids(self, organization_ids: list[UUID]) -> list[OrganizationDTO]:
        if not organization_ids:
            return []

        result = await self.session.execute(
            select(Organization).where(Organization.id.in_(organization_ids)).order_by(Organization.name),
        )
        return self._to_dtos(result.scalars().all())
