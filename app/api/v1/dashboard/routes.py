from datetime import date
from typing import Annotated

from api.dependencies import get_analytics_service, get_current_organization
from api.routing import ServiceErrorRoute
from fastapi import APIRouter, Depends, Query
from schemas import DashboardSummaryInput, DashboardSummaryResponse, OrganizationDTO
from services import AnalyticsService

__all__ = ["router"]

router = APIRouter(prefix="/dashboard", tags=["dashboard"], route_class=ServiceErrorRoute)


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    target_date: Annotated[date, Query(alias="date")],
) -> DashboardSummaryResponse:
    return await service.get_dashboard_summary(
        DashboardSummaryInput(organization_id=organization.id, target_date=target_date),
    )
