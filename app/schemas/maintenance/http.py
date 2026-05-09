from datetime import date
from decimal import Decimal
from uuid import UUID

from db.models import Currency, ServiceType
from pydantic import BaseModel, Field
from schemas.base.common import BaseEntityResponse

__all__ = [
    "MaintenanceRecordCreateRequest",
    "MaintenanceRecordResponse",
    "MaintenanceRecordUpdateRequest",
    "MaintenanceScheduleCompleteRequest",
    "MaintenanceScheduleCreateRequest",
    "MaintenanceScheduleResponse",
    "MaintenanceScheduleUpdateRequest",
]


class MaintenanceRecordCreateRequest(BaseModel):
    car_id: UUID
    service_date: date
    service_type: ServiceType
    description: str = Field(min_length=1)
    mileage_at_service: int = Field(ge=0)
    cost: Decimal = Field(ge=0)
    currency: Currency
    provider: str | None = Field(default=None, max_length=255)
    complete_schedule_id: UUID | None = None


class MaintenanceRecordUpdateRequest(BaseModel):
    service_date: date = None
    service_type: ServiceType = None
    description: str = Field(default=None, min_length=1)
    mileage_at_service: int = Field(default=None, ge=0)
    cost: Decimal = Field(default=None, ge=0)
    currency: Currency | None = None
    provider: str | None = Field(default=None, max_length=255)


class MaintenanceScheduleCreateRequest(BaseModel):
    car_id: UUID
    service_type: ServiceType
    scheduled_date: date | None = None
    scheduled_mileage: int | None = Field(default=None, ge=0)
    interval_km: int | None = Field(default=None, gt=0)


class MaintenanceScheduleUpdateRequest(BaseModel):
    service_type: ServiceType = None
    scheduled_date: date | None = None
    scheduled_mileage: int | None = Field(default=None, ge=0)
    interval_km: int | None = Field(default=None, gt=0)


class MaintenanceScheduleCompleteRequest(BaseModel):
    maintenance_record_id: UUID


class MaintenanceRecordResponse(BaseEntityResponse):
    organization_id: UUID
    car_id: UUID
    service_date: date
    service_type: ServiceType
    description: str
    mileage_at_service: int
    cost: Decimal
    currency: Currency
    provider: str | None


class MaintenanceScheduleResponse(BaseEntityResponse):
    organization_id: UUID
    car_id: UUID
    service_type: ServiceType
    scheduled_date: date | None
    scheduled_mileage: int | None
    interval_km: int | None
    is_completed: bool
    maintenance_record_id: UUID | None
