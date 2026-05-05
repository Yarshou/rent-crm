from datetime import date
from typing import Annotated
from uuid import UUID

from api.dependencies import get_current_organization, get_maintenance_service
from api.routing import ServiceErrorRoute
from db.models import ServiceType
from fastapi import APIRouter, Depends, Query, Response, status
from schemas import (
    MaintenanceRecordCreateInput,
    MaintenanceRecordCreateRequest,
    MaintenanceRecordDeleteInput,
    MaintenanceRecordGetInput,
    MaintenanceRecordListInput,
    MaintenanceRecordResponse,
    MaintenanceRecordUpdateInput,
    MaintenanceRecordUpdateRequest,
    MaintenanceScheduleCompleteInput,
    MaintenanceScheduleCompleteRequest,
    MaintenanceScheduleCreateInput,
    MaintenanceScheduleCreateRequest,
    MaintenanceScheduleDeleteInput,
    MaintenanceScheduleDueByDateInput,
    MaintenanceScheduleDueByMileageInput,
    MaintenanceScheduleGetInput,
    MaintenanceScheduleListInput,
    MaintenanceScheduleResponse,
    MaintenanceScheduleUpdateInput,
    MaintenanceScheduleUpdateRequest,
    OrganizationDTO,
)
from services import MaintenanceService

__all__ = ["router"]

router = APIRouter(
    prefix="/maintenance",
    tags=["maintenance"],
    route_class=ServiceErrorRoute,
)


@router.get("/records", response_model=list[MaintenanceRecordResponse])
async def list_maintenance_records(
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
    car_ids: Annotated[list[UUID] | None, Query()] = None,
    service_types: Annotated[list[ServiceType] | None, Query()] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> list[MaintenanceRecordResponse]:
    records = await service.list_records(
        MaintenanceRecordListInput(
            organization_id=organization.id,
            car_ids=car_ids,
            service_types=service_types,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=limit,
        ),
    )
    return [MaintenanceRecordResponse.model_validate(record) for record in records]


@router.post("/records", response_model=MaintenanceRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance_record(
    payload: MaintenanceRecordCreateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> MaintenanceRecordResponse:
    record = await service.create_record(
        MaintenanceRecordCreateInput(
            organization_id=organization.id,
            car_id=payload.car_id,
            service_date=payload.service_date,
            service_type=payload.service_type,
            description=payload.description,
            mileage_at_service=payload.mileage_at_service,
            cost=payload.cost,
            provider=payload.provider,
            complete_schedule_id=payload.complete_schedule_id,
        ),
    )
    return MaintenanceRecordResponse.model_validate(record)


@router.get("/records/{maintenance_record_id}", response_model=MaintenanceRecordResponse)
async def get_maintenance_record(
    maintenance_record_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> MaintenanceRecordResponse:
    record = await service.get_record(
        MaintenanceRecordGetInput(
            organization_id=organization.id,
            maintenance_record_id=maintenance_record_id,
        ),
    )
    return MaintenanceRecordResponse.model_validate(record)


@router.patch("/records/{maintenance_record_id}", response_model=MaintenanceRecordResponse)
async def update_maintenance_record(
    maintenance_record_id: UUID,
    payload: MaintenanceRecordUpdateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> MaintenanceRecordResponse:
    record = await service.update_record(
        MaintenanceRecordUpdateInput(
            organization_id=organization.id,
            maintenance_record_id=maintenance_record_id,
            **payload.model_dump(exclude_unset=True),
        ),
    )
    return MaintenanceRecordResponse.model_validate(record)


@router.delete("/records/{maintenance_record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_maintenance_record(
    maintenance_record_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> Response:
    await service.delete_record(
        MaintenanceRecordDeleteInput(
            organization_id=organization.id,
            maintenance_record_id=maintenance_record_id,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/schedules", response_model=list[MaintenanceScheduleResponse])
async def list_maintenance_schedules(
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
    car_ids: Annotated[list[UUID] | None, Query()] = None,
    service_types: Annotated[list[ServiceType] | None, Query()] = None,
    is_completed: bool | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> list[MaintenanceScheduleResponse]:
    schedules = await service.list_schedules(
        MaintenanceScheduleListInput(
            organization_id=organization.id,
            car_ids=car_ids,
            service_types=service_types,
            is_completed=is_completed,
            offset=offset,
            limit=limit,
        ),
    )
    return [MaintenanceScheduleResponse.model_validate(schedule) for schedule in schedules]


@router.post("/schedules", response_model=MaintenanceScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance_schedule(
    payload: MaintenanceScheduleCreateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> MaintenanceScheduleResponse:
    schedule = await service.create_schedule(
        MaintenanceScheduleCreateInput(
            organization_id=organization.id,
            car_id=payload.car_id,
            service_type=payload.service_type,
            scheduled_date=payload.scheduled_date,
            scheduled_mileage=payload.scheduled_mileage,
            interval_km=payload.interval_km,
        ),
    )
    return MaintenanceScheduleResponse.model_validate(schedule)


@router.get("/schedules/due-by-date", response_model=list[MaintenanceScheduleResponse])
async def list_maintenance_schedules_due_by_date(
    due_date: date,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> list[MaintenanceScheduleResponse]:
    schedules = await service.list_due_by_date(
        MaintenanceScheduleDueByDateInput(organization_id=organization.id, due_date=due_date),
    )
    return [MaintenanceScheduleResponse.model_validate(schedule) for schedule in schedules]


@router.get("/cars/{car_id}/schedules/due-by-mileage", response_model=list[MaintenanceScheduleResponse])
async def list_maintenance_schedules_due_by_mileage(
    car_id: UUID,
    mileage: Annotated[int, Query(ge=0)],
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> list[MaintenanceScheduleResponse]:
    schedules = await service.list_due_by_mileage(
        MaintenanceScheduleDueByMileageInput(
            organization_id=organization.id,
            car_id=car_id,
            mileage=mileage,
        ),
    )
    return [MaintenanceScheduleResponse.model_validate(schedule) for schedule in schedules]


@router.get("/schedules/{maintenance_schedule_id}", response_model=MaintenanceScheduleResponse)
async def get_maintenance_schedule(
    maintenance_schedule_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> MaintenanceScheduleResponse:
    schedule = await service.get_schedule(
        MaintenanceScheduleGetInput(
            organization_id=organization.id,
            maintenance_schedule_id=maintenance_schedule_id,
        ),
    )
    return MaintenanceScheduleResponse.model_validate(schedule)


@router.patch("/schedules/{maintenance_schedule_id}", response_model=MaintenanceScheduleResponse)
async def update_maintenance_schedule(
    maintenance_schedule_id: UUID,
    payload: MaintenanceScheduleUpdateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> MaintenanceScheduleResponse:
    schedule = await service.update_schedule(
        MaintenanceScheduleUpdateInput(
            organization_id=organization.id,
            maintenance_schedule_id=maintenance_schedule_id,
            **payload.model_dump(exclude_unset=True),
        ),
    )
    return MaintenanceScheduleResponse.model_validate(schedule)


@router.post("/schedules/{maintenance_schedule_id}/complete", response_model=MaintenanceScheduleResponse)
async def complete_maintenance_schedule(
    maintenance_schedule_id: UUID,
    payload: MaintenanceScheduleCompleteRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> MaintenanceScheduleResponse:
    schedule = await service.complete_schedule(
        MaintenanceScheduleCompleteInput(
            organization_id=organization.id,
            maintenance_schedule_id=maintenance_schedule_id,
            maintenance_record_id=payload.maintenance_record_id,
        ),
    )
    return MaintenanceScheduleResponse.model_validate(schedule)


@router.delete("/schedules/{maintenance_schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_maintenance_schedule(
    maintenance_schedule_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
) -> Response:
    await service.delete_schedule(
        MaintenanceScheduleDeleteInput(
            organization_id=organization.id,
            maintenance_schedule_id=maintenance_schedule_id,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
