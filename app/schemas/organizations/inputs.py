from uuid import UUID

from schemas.base import MutableDTO

__all__ = [
    "OrganizationCreateForUserInput",
    "OrganizationCreateInput",
    "OrganizationDeleteInput",
    "OrganizationGetInput",
    "OrganizationListByIdsInput",
    "OrganizationListInput",
    "OrganizationUpdateInput",
]


class OrganizationGetInput(MutableDTO):
    organization_id: UUID


class OrganizationListInput(MutableDTO):
    offset: int = 0
    limit: int | None = None


class OrganizationListByIdsInput(MutableDTO):
    organization_ids: list[UUID]


class OrganizationCreateInput(MutableDTO):
    name: str


class OrganizationCreateForUserInput(MutableDTO):
    name: str
    user_id: UUID


class OrganizationUpdateInput(MutableDTO):
    organization_id: UUID
    name: str


class OrganizationDeleteInput(MutableDTO):
    organization_id: UUID
