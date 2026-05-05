from datetime import date
from typing import Annotated

from api.dependencies import get_analytics_service, get_current_organization
from api.routing import ServiceErrorRoute
from fastapi import APIRouter, Depends
from schemas import CalendarRangeInput, CalendarResponse, OrganizationDTO
from services import AnalyticsService

__all__ = ["router"]

router = APIRouter(prefix="/calendar", tags=["calendar"], route_class=ServiceErrorRoute)


@router.get("", response_model=CalendarResponse)
async def get_calendar(
    date_from: date,
    date_to: date,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> CalendarResponse:
    return await service.get_calendar(
        CalendarRangeInput(organization_id=organization.id, date_from=date_from, date_to=date_to),
    )
