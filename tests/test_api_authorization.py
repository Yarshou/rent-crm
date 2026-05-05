import asyncio
import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest

os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("APP_PORT", "8000")
os.environ.setdefault("POSTGRES_DB", "rent_crm")
os.environ.setdefault("POSTGRES_HOST", "postgres")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("JWT_ACCESS_SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_ACCESS_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_EXPIRE", "15m")
os.environ.setdefault("JWT_REFRESH_ALGORITHM", "HS256")
os.environ.setdefault("JWT_REFRESH_EXPIRE", "7d")

from api.dependencies import get_current_organization, require_organization_access, require_super_admin
from api.v1 import bookings, calendar, cars, dashboard, insurance, maintenance, organizations, reports, users
from api.v1.organizations.routes import list_organizations
from schemas import (
    OrganizationAccessInput,
    OrganizationDTO,
    UserDTO,
    UserListOrganizationsInput,
)
from services import ServiceNotFoundError


def run(coro):
    return asyncio.run(coro)


def make_user_dto(*, is_super_admin: bool = False) -> UserDTO:
    return UserDTO(
        id=uuid4(),
        email="user@example.com",
        password_hash="hashed",
        full_name="Test User",
        is_super_admin=is_super_admin,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class OrganizationAccessStub:
    def __init__(self, *, organizations: list[OrganizationDTO] | None = None, has_access: bool = True) -> None:
        self.organizations = organizations or []
        self.has_access = has_access

    async def ensure_organization_access(self, input: OrganizationAccessInput) -> None:
        if not self.has_access:
            raise ServiceNotFoundError("Organization not found.")

    async def list_organizations(self, input: UserListOrganizationsInput) -> list[OrganizationDTO]:
        if input.limit is None:
            return self.organizations[input.offset :]
        return self.organizations[input.offset : input.offset + input.limit]


def dependency_calls(route) -> set[object]:
    return {dependency.call for dependency in route.dependant.dependencies}


def test_organization_scoped_routers_require_organization_access() -> None:
    for feature_router in (cars.router, bookings.router, maintenance.router, insurance.router):
        for route in feature_router.routes:
            if route.path.startswith("/organizations/{organization_id}"):
                assert require_organization_access in dependency_calls(route)


def test_current_context_aggregate_routers_require_current_organization() -> None:
    for feature_router in (dashboard.router, calendar.router, reports.router, cars.router):
        for route in feature_router.routes:
            if not route.path.startswith("/organizations/{organization_id}"):
                assert get_current_organization in dependency_calls(route)


def test_organization_detail_routes_require_organization_access() -> None:
    protected_paths = {
        "/organizations/{organization_id}",
    }

    for route in organizations.router.routes:
        if route.path in protected_paths:
            assert require_organization_access in dependency_calls(route)


def test_user_admin_router_requires_super_admin() -> None:
    for route in users.router.routes:
        assert require_super_admin in dependency_calls(route)


def test_require_organization_access_rejects_unrelated_organization() -> None:
    async def scenario() -> None:
        with pytest.raises(ServiceNotFoundError):
            await require_organization_access(
                organization_id=uuid4(),
                current_user=make_user_dto(),
                user_service=OrganizationAccessStub(has_access=False),
            )

    run(scenario())


def test_list_organizations_returns_only_current_user_organizations() -> None:
    async def scenario() -> None:
        organization = OrganizationDTO(
            id=uuid4(),
            name="Allowed Org",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        response = await list_organizations(
            current_user=make_user_dto(),
            user_service=OrganizationAccessStub(organizations=[organization]),
        )

        assert [item.id for item in response] == [organization.id]

    run(scenario())
