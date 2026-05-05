from __future__ import annotations

from db.models import OrganizationRole
from schemas.organizations import (
    OrganizationCreateForUserInput,
    OrganizationCreateInput,
    OrganizationDeleteInput,
    OrganizationDTO,
    OrganizationGetInput,
    OrganizationListByIdsInput,
    OrganizationListInput,
    OrganizationUpdateInput,
)

from ..common import ServiceConflictError, ServiceNotFoundError, UnitOfWorkFactory

__all__ = ["OrganizationService"]


class OrganizationService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get(self, input: OrganizationGetInput) -> OrganizationDTO:
        async with self._uow_factory() as uow:
            organization = await uow.organizations.get(input.organization_id)
            if organization is None:
                raise ServiceNotFoundError("Organization not found.")
            return organization

    async def list(self, input: OrganizationListInput) -> list[OrganizationDTO]:
        async with self._uow_factory() as uow:
            return await uow.organizations.list(offset=input.offset, limit=input.limit)

    async def list_by_ids(self, input: OrganizationListByIdsInput) -> list[OrganizationDTO]:
        async with self._uow_factory() as uow:
            return await uow.organizations.list_by_ids(input.organization_ids)

    async def create(self, input: OrganizationCreateInput) -> OrganizationDTO:
        async with self._uow_factory() as uow:
            existing = await uow.organizations.get_by_name(input.name)
            if existing is not None:
                raise ServiceConflictError("Organization with this name already exists.")

            organization = await uow.organizations.create(name=input.name)
            await uow.commit()
            return organization

    async def create_for_user(self, input: OrganizationCreateForUserInput) -> OrganizationDTO:
        async with self._uow_factory() as uow:
            user = await uow.users.get(input.user_id)
            if user is None:
                raise ServiceNotFoundError("User not found.")

            existing = await uow.organizations.get_by_name(input.name)
            if existing is not None:
                raise ServiceConflictError("Organization with this name already exists.")

            organization = await uow.organizations.create(name=input.name)
            await uow.organization_members.create(
                organization_id=organization.id,
                user_id=user.id,
                role=OrganizationRole.owner,
            )
            await uow.commit()
            return organization

    async def update(self, input: OrganizationUpdateInput) -> OrganizationDTO:
        async with self._uow_factory() as uow:
            organization = await uow.organizations.get(input.organization_id)
            if organization is None:
                raise ServiceNotFoundError("Organization not found.")

            existing = await uow.organizations.get_by_name(input.name)
            if existing is not None and existing.id != organization.id:
                raise ServiceConflictError("Organization with this name already exists.")

            updated = await uow.organizations.update(input.organization_id, name=input.name)
            if updated is None:
                raise ServiceNotFoundError("Organization not found.")
            await uow.commit()
            return updated

    async def delete(self, input: OrganizationDeleteInput) -> None:
        async with self._uow_factory() as uow:
            deleted = await uow.organizations.delete_by_id(input.organization_id)
            if not deleted:
                raise ServiceNotFoundError("Organization not found.")

            await uow.commit()
