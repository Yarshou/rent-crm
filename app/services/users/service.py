from config.security import create_password_hash, verify_password
from schemas.organizations import OrganizationDTO
from schemas.users import (
    OrganizationAccessInput,
    OrganizationMemberDTO,
    OrganizationMembershipCreateInput,
    UserAuthenticateInput,
    UserByEmailInput,
    UserCreateInput,
    UserDTO,
    UserGetInput,
    UserListMembershipsInput,
    UserListOrganizationsInput,
    UserPasswordUpdateInput,
    UserProfileUpdateInput,
    UserRegisterInput,
)

from ..common import ServiceConflictError, ServiceNotFoundError, ServiceUnauthorizedError, UnitOfWorkFactory

__all__ = ["UserService"]


class UserService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get(self, input: UserGetInput) -> UserDTO:
        async with self._uow_factory() as uow:
            user = await uow.users.get(input.user_id)
            if user is None:
                raise ServiceNotFoundError("User not found.")
            return user

    async def get_by_email(self, input: UserByEmailInput) -> UserDTO:
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_email(input.email)
            if user is None:
                raise ServiceNotFoundError("User not found.")
            return user

    async def create(self, input: UserCreateInput) -> UserDTO:
        async with self._uow_factory() as uow:
            existing = await uow.users.get_by_email(input.email)
            if existing is not None:
                raise ServiceConflictError("User with this email already exists.")

            user = await uow.users.create(
                email=input.email,
                password_hash=input.password_hash,
                full_name=input.full_name,
                is_super_admin=input.is_super_admin,
            )
            await uow.commit()
            return user

    async def register(self, input: UserRegisterInput) -> UserDTO:
        return await self.create(
            UserCreateInput(
                email=input.email,
                password_hash=create_password_hash(input.password),
                full_name=input.full_name,
                is_super_admin=False,
            ),
        )

    async def authenticate(self, input: UserAuthenticateInput) -> UserDTO:
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_email(input.email)
            if user is None:
                raise ServiceUnauthorizedError("Invalid email or password.")

            try:
                is_password_valid = verify_password(input.password, user.password_hash)
            except ValueError as exception:
                raise ServiceUnauthorizedError("Invalid email or password.") from exception

            if not is_password_valid:
                raise ServiceUnauthorizedError("Invalid email or password.")

            return user

    async def update_profile(self, input: UserProfileUpdateInput) -> UserDTO:
        async with self._uow_factory() as uow:
            updated = await uow.users.update(input.user_id, full_name=input.full_name)
            if updated is None:
                raise ServiceNotFoundError("User not found.")
            await uow.commit()
            return updated

    async def update_password_hash(self, input: UserPasswordUpdateInput) -> UserDTO:
        async with self._uow_factory() as uow:
            updated = await uow.users.update(input.user_id, password_hash=input.password_hash)
            if updated is None:
                raise ServiceNotFoundError("User not found.")
            await uow.commit()
            return updated

    async def add_to_organization(self, input: OrganizationMembershipCreateInput) -> OrganizationMemberDTO:
        async with self._uow_factory() as uow:
            user = await uow.users.get(input.user_id)
            if user is None:
                raise ServiceNotFoundError("User not found.")

            organization = await uow.organizations.get(input.organization_id)
            if organization is None:
                raise ServiceNotFoundError("Organization not found.")

            existing = await uow.organization_members.get_by_user_and_organization(
                user_id=input.user_id,
                organization_id=input.organization_id,
            )
            if existing is not None:
                raise ServiceConflictError("User is already a member of this organization.")

            member = await uow.organization_members.create(
                user_id=input.user_id,
                organization_id=input.organization_id,
                role=input.role,
            )
            await uow.commit()
            return member

    async def list_memberships(self, input: UserListMembershipsInput) -> list[OrganizationMemberDTO]:
        async with self._uow_factory() as uow:
            user = await uow.users.get(input.user_id)
            if user is None:
                raise ServiceNotFoundError("User not found.")

            return await uow.organization_members.list_by_user(input.user_id)

    async def list_organizations(self, input: UserListOrganizationsInput) -> list[OrganizationDTO]:
        async with self._uow_factory() as uow:
            user = await uow.users.get(input.user_id)
            if user is None:
                raise ServiceNotFoundError("User not found.")

            if user.is_super_admin:
                return await uow.organizations.list(offset=input.offset, limit=input.limit)

            memberships = await uow.organization_members.list_by_user(input.user_id)
            organizations = await uow.organizations.list_by_ids(
                [membership.organization_id for membership in memberships],
            )
            if input.limit is None:
                return organizations[input.offset :]
            return organizations[input.offset : input.offset + input.limit]

    async def ensure_organization_access(self, input: OrganizationAccessInput) -> None:
        async with self._uow_factory() as uow:
            user = await uow.users.get(input.user_id)
            if user is None:
                raise ServiceNotFoundError("User not found.")

            organization = await uow.organizations.get(input.organization_id)
            if organization is None:
                raise ServiceNotFoundError("Organization not found.")

            if user.is_super_admin:
                return

            has_access = await uow.organization_members.user_has_organization_access(
                user_id=input.user_id,
                organization_id=input.organization_id,
            )
            if not has_access:
                raise ServiceNotFoundError("Organization not found.")
