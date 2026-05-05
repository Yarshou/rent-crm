from typing import Annotated
from uuid import UUID

from config.security import decode_access_token, get_unauthorized_exception
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from repositories import UnitOfWork
from schemas.organizations import OrganizationDTO
from schemas.users import (
    UserDTO,
    UserGetInput,
    UserListOrganizationsInput,
)
from services import (
    AnalyticsService,
    BookingService,
    CarService,
    InsuranceService,
    MaintenanceService,
    OrganizationService,
    SearchService,
    ServiceNotFoundError,
    UserService,
)

__all__ = [
    "bearer_scheme",
    "get_analytics_service",
    "get_booking_service",
    "get_car_service",
    "get_current_organization",
    "get_current_user",
    "get_insurance_service",
    "get_maintenance_service",
    "get_organization_service",
    "get_search_service",
    "get_uow",
    "get_user_service",
    "require_super_admin",
]

bearer_scheme = HTTPBearer(auto_error=False)


def get_uow() -> UnitOfWork:
    from config.settings import async_session_maker

    return UnitOfWork(async_session_maker)


def get_organization_service() -> OrganizationService:
    return OrganizationService(get_uow)


def get_user_service() -> UserService:
    return UserService(get_uow)


def get_car_service() -> CarService:
    return CarService(get_uow)


def get_booking_service() -> BookingService:
    return BookingService(get_uow)


def get_maintenance_service() -> MaintenanceService:
    return MaintenanceService(get_uow)


def get_insurance_service() -> InsuranceService:
    return InsuranceService(get_uow)


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(get_uow)


def get_search_service() -> SearchService:
    return SearchService(get_uow)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserDTO:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise get_unauthorized_exception()

    token_payload = decode_access_token(token=credentials.credentials)

    try:
        user_id = UUID(token_payload.sub)
    except ValueError as exception:
        raise get_unauthorized_exception() from exception

    try:
        return await user_service.get(UserGetInput(user_id=user_id))
    except ServiceNotFoundError as exception:
        raise get_unauthorized_exception() from exception


async def require_super_admin(
    current_user: Annotated[UserDTO, Depends(get_current_user)],
) -> UserDTO:
    if not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions.")
    return current_user


async def get_current_organization(
    current_user: Annotated[UserDTO, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> OrganizationDTO:
    organizations = await user_service.list_organizations(
        UserListOrganizationsInput(user_id=current_user.id, limit=1),
    )
    if not organizations:
        raise ServiceNotFoundError("Organization not found.")
    return organizations[0]
