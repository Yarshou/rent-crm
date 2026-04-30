from uuid import UUID

from db.models import OrganizationMember, User
from repositories import BaseRepository
from sqlalchemy import select

__all__ = ["OrganizationMemberRepository", "UserRepository"]


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


class OrganizationMemberRepository(BaseRepository[OrganizationMember]):
    model = OrganizationMember

    async def get_by_user_and_organization(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
    ) -> OrganizationMember | None:
        result = await self.session.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id,
            ),
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[OrganizationMember]:
        result = await self.session.execute(
            select(OrganizationMember).where(OrganizationMember.user_id == user_id).order_by(OrganizationMember.created_at),
        )
        return list(result.scalars().all())

    async def list_by_organization(self, organization_id: UUID) -> list[OrganizationMember]:
        result = await self.session.execute(
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == organization_id)
            .order_by(OrganizationMember.created_at),
        )
        return list(result.scalars().all())

    async def user_has_organization_access(self, *, user_id: UUID, organization_id: UUID) -> bool:
        result = await self.session.execute(
            select(OrganizationMember.id)
            .where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id,
            )
            .limit(1),
        )
        return result.scalar_one_or_none() is not None
