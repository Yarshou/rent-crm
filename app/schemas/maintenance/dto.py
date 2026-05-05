from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from db.models import ServiceType
from schemas.base import ImmutableDTO

__all__ = ["MaintenanceRecordDTO", "MaintenanceScheduleDTO"]


class MaintenanceRecordDTO(ImmutableDTO):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    organization_id: UUID
    car_id: UUID
    service_date: date
    service_type: ServiceType
    description: str
    mileage_at_service: int
    cost: Decimal
    provider: str | None = None


class MaintenanceScheduleDTO(ImmutableDTO):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    organization_id: UUID
    car_id: UUID
    service_type: ServiceType
    scheduled_date: date | None = None
    scheduled_mileage: int | None = None
    interval_km: int | None = None
    is_completed: bool
    maintenance_record_id: UUID | None = None
