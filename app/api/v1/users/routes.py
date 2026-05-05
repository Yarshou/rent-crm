from typing import Annotated
from uuid import UUID

from api.dependencies import get_user_service, require_super_admin
from api.routing import ServiceErrorRoute
from fastapi import APIRouter, Depends, Query, status
from schemas import (
    OrganizationMemberCreateRequest,
    OrganizationMemberResponse,
    OrganizationMembershipCreateInput,
    OrganizationResponse,
    UserByEmailInput,
    UserCreateInput,
    UserCreateRequest,
    UserGetInput,
    UserListMembershipsInput,
    UserListOrganizationsInput,
    UserPasswordUpdateInput,
    UserPasswordUpdateRequest,
    UserProfileUpdateInput,
    UserProfileUpdateRequest,
    UserResponse,
)
from services import UserService

__all__ = ["router"]

router = APIRouter(
    prefix="/users",
    tags=["users"],
    route_class=ServiceErrorRoute,
    dependencies=[Depends(require_super_admin)],
)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    user = await service.create(UserCreateInput(**payload.model_dump()))
    return UserResponse.model_validate(user)


@router.get("/by-email", response_model=UserResponse)
async def get_user_by_email(
    email: Annotated[str, Query(min_length=1, max_length=255)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    user = await service.get_by_email(UserByEmailInput(email=email))
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    user = await service.get(UserGetInput(user_id=user_id))
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/profile", response_model=UserResponse)
async def update_user_profile(
    user_id: UUID,
    payload: UserProfileUpdateRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    user = await service.update_profile(UserProfileUpdateInput(user_id=user_id, full_name=payload.full_name))
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/password", response_model=UserResponse)
async def update_user_password(
    user_id: UUID,
    payload: UserPasswordUpdateRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    user = await service.update_password_hash(
        UserPasswordUpdateInput(user_id=user_id, password_hash=payload.password_hash),
    )
    return UserResponse.model_validate(user)


@router.post("/{user_id}/organizations", response_model=OrganizationMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_user_to_organization(
    user_id: UUID,
    payload: OrganizationMemberCreateRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> OrganizationMemberResponse:
    member = await service.add_to_organization(
        OrganizationMembershipCreateInput(
            user_id=user_id,
            organization_id=payload.organization_id,
            role=payload.role,
        ),
    )
    return OrganizationMemberResponse.model_validate(member)


@router.get("/{user_id}/memberships", response_model=list[OrganizationMemberResponse])
async def list_user_memberships(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
) -> list[OrganizationMemberResponse]:
    members = await service.list_memberships(UserListMembershipsInput(user_id=user_id))
    return [OrganizationMemberResponse.model_validate(member) for member in members]


@router.get("/{user_id}/organizations", response_model=list[OrganizationResponse])
async def list_user_organizations(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
) -> list[OrganizationResponse]:
    organizations = await service.list_organizations(UserListOrganizationsInput(user_id=user_id))
    return [OrganizationResponse.model_validate(organization) for organization in organizations]
