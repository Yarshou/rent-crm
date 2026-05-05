from datetime import date
from typing import Annotated
from uuid import UUID

from api.dependencies import get_analytics_service, get_current_organization
from api.routing import ServiceErrorRoute
from fastapi import APIRouter, Depends
from schemas import CarDetailsInput, CarDetailsResponse, OrganizationDTO
from services import AnalyticsService

__all__ = ["router"]

router = APIRouter(prefix="/cars", tags=["cars"], route_class=ServiceErrorRoute)


@router.get("/{car_id}/details", response_model=CarDetailsResponse)
async def get_car_details(
    car_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> CarDetailsResponse:
    return await service.get_car_details(
        CarDetailsInput(organization_id=organization.id, car_id=car_id, today=date.today()),
    )
