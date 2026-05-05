from typing import Annotated

from api.dependencies import get_current_user, get_user_service
from api.routing import ServiceErrorRoute
from config.security import create_access_token, create_refresh_token
from fastapi import APIRouter, Depends, status
from schemas import (
    AuthResponse,
    CurrentUserResponse,
    LoginRequest,
    OrganizationContextResponse,
    RegisterUserRequest,
    UserAuthenticateInput,
    UserDTO,
    UserListOrganizationsInput,
    UserRegisterInput,
)
from services import ServiceNotFoundError, UserService

__all__ = ["router"]

router = APIRouter(prefix="/auth", tags=["auth"], route_class=ServiceErrorRoute)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: RegisterUserRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> AuthResponse:
    user = await service.register(
        UserRegisterInput(email=payload.email, password=payload.password, full_name=payload.full_name),
    )
    return AuthResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.post("/login", response_model=AuthResponse)
async def login_user(
    payload: LoginRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> AuthResponse:
    user = await service.authenticate(UserAuthenticateInput(email=payload.email, password=payload.password))
    return AuthResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(
    current_user: Annotated[UserDTO, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> CurrentUserResponse:
    organizations = await service.list_organizations(
        UserListOrganizationsInput(user_id=current_user.id, limit=1),
    )
    if not organizations:
        raise ServiceNotFoundError("Organization not found.")

    organization = organizations[0]
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_super_admin=current_user.is_super_admin,
        organization=OrganizationContextResponse(id=organization.id, name=organization.name),
    )
