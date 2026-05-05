from typing import Annotated

from api.dependencies import get_current_organization, get_search_service
from api.routing import ServiceErrorRoute
from fastapi import APIRouter, Depends, Query
from schemas import OrganizationDTO, SearchInput, SearchResponse
from services import SearchService

__all__ = ["router"]

router = APIRouter(prefix="/search", tags=["search"], route_class=ServiceErrorRoute)


@router.get("", response_model=SearchResponse)
async def search(
    q: Annotated[str, Query(min_length=1, max_length=200)],
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[SearchService, Depends(get_search_service)],
    limit: Annotated[int, Query(gt=0, le=20)] = 10,
) -> SearchResponse:
    return await service.search(SearchInput(organization_id=organization.id, q=q, limit=limit))
