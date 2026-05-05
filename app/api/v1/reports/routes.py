from typing import Annotated

from api.dependencies import get_analytics_service, get_current_organization
from api.routing import ServiceErrorRoute
from fastapi import APIRouter, Depends, Query
from schemas import OrganizationDTO, ReportsSummaryInput, ReportsSummaryResponse
from services import AnalyticsService

__all__ = ["router"]

router = APIRouter(prefix="/reports", tags=["reports"], route_class=ServiceErrorRoute)


@router.get("/summary", response_model=ReportsSummaryResponse)
async def get_reports_summary(
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    year: Annotated[int, Query(ge=2000, le=2100)],
) -> ReportsSummaryResponse:
    return await service.get_reports_summary(
        ReportsSummaryInput(organization_id=organization.id, year=year),
    )
