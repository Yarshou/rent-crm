from typing import Annotated

from api.dependencies import get_current_organization, get_current_user, get_organization_service, get_user_service
from api.routing import ServiceErrorRoute
from fastapi import APIRouter, Depends, Query, Response, status
from schemas import (
    OrganizationCreateForUserInput,
    OrganizationCreateRequest,
    OrganizationDeleteInput,
    OrganizationDTO,
    OrganizationGetInput,
    OrganizationResponse,
    OrganizationUpdateInput,
    OrganizationUpdateRequest,
    UserDTO,
    UserListOrganizationsInput,
)
from services import OrganizationService, UserService

__all__ = ["router"]

router = APIRouter(prefix="/organizations", tags=["organizations"], route_class=ServiceErrorRoute)


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    current_user: Annotated[UserDTO, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> list[OrganizationResponse]:
    organizations = await user_service.list_organizations(
        UserListOrganizationsInput(user_id=current_user.id, offset=offset, limit=limit),
    )
    return [OrganizationResponse.model_validate(organization) for organization in organizations]


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreateRequest,
    current_user: Annotated[UserDTO, Depends(get_current_user)],
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> OrganizationResponse:
    organization = await service.create_for_user(
        OrganizationCreateForUserInput(name=payload.name, user_id=current_user.id),
    )
    return OrganizationResponse.model_validate(organization)


@router.get("/me", response_model=OrganizationResponse)
async def get_organization(
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> OrganizationResponse:
    result = await service.get(OrganizationGetInput(organization_id=organization.id))
    return OrganizationResponse.model_validate(result)


@router.patch("/me", response_model=OrganizationResponse)
async def update_organization(
    payload: OrganizationUpdateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> OrganizationResponse:
    result = await service.update(
        OrganizationUpdateInput(organization_id=organization.id, name=payload.name),
    )
    return OrganizationResponse.model_validate(result)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[OrganizationService, Depends(get_organization_service)],
) -> Response:
    await service.delete(OrganizationDeleteInput(organization_id=organization.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
