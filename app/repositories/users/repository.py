from uuid import UUID

from db.models import OrganizationMember, User
from repositories import BaseRepository
from schemas.users import OrganizationMemberDTO, UserDTO
from sqlalchemy import select

__all__ = ["OrganizationMemberRepository", "UserRepository"]


class UserRepository(BaseRepository[User, UserDTO]):
    model = User
    dto = UserDTO

    async def get_by_email(self, email: str) -> UserDTO | None:
        result = await self.session.execute(select(User).where(User.email == email))
        instance = result.scalar_one_or_none()
        return self._to_dto(instance) if instance is not None else None


class OrganizationMemberRepository(BaseRepository[OrganizationMember, OrganizationMemberDTO]):
    model = OrganizationMember
    dto = OrganizationMemberDTO

    async def get_by_user_and_organization(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
    ) -> OrganizationMemberDTO | None:
        result = await self.session.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id,
            ),
        )
        instance = result.scalar_one_or_none()
        return self._to_dto(instance) if instance is not None else None

    async def list_by_user(self, user_id: UUID) -> list[OrganizationMemberDTO]:
        result = await self.session.execute(
            select(OrganizationMember).where(OrganizationMember.user_id == user_id).order_by(OrganizationMember.created_at),
        )
        return self._to_dtos(result.scalars().all())

    async def list_by_organization(self, organization_id: UUID) -> list[OrganizationMemberDTO]:
        result = await self.session.execute(
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == organization_id)
            .order_by(OrganizationMember.created_at),
        )
        return self._to_dtos(result.scalars().all())

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
