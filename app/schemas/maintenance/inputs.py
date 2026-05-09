from datetime import date
from decimal import Decimal
from uuid import UUID

from db.models import Currency, ServiceType
from schemas.base import MutableDTO

__all__ = [
    "MaintenanceRecordCreateInput",
    "MaintenanceRecordDeleteInput",
    "MaintenanceRecordGetInput",
    "MaintenanceRecordListInput",
    "MaintenanceRecordUpdateInput",
    "MaintenanceScheduleCompleteInput",
    "MaintenanceScheduleCreateInput",
    "MaintenanceScheduleDeleteInput",
    "MaintenanceScheduleDueByDateInput",
    "MaintenanceScheduleDueByMileageInput",
    "MaintenanceScheduleGetInput",
    "MaintenanceScheduleListInput",
    "MaintenanceScheduleUpdateInput",
]


class MaintenanceRecordGetInput(MutableDTO):
    organization_id: UUID
    maintenance_record_id: UUID


class MaintenanceRecordListInput(MutableDTO):
    organization_id: UUID
    car_ids: list[UUID] | None = None
    service_types: list[ServiceType] | None = None
    date_from: date | None = None
    date_to: date | None = None
    offset: int = 0
    limit: int | None = None


class MaintenanceRecordCreateInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    service_date: date
    service_type: ServiceType
    description: str
    mileage_at_service: int
    cost: Decimal
    currency: Currency
    provider: str | None = None
    complete_schedule_id: UUID | None = None


class MaintenanceRecordUpdateInput(MutableDTO):
    organization_id: UUID
    maintenance_record_id: UUID
    service_date: date | None = None
    service_type: ServiceType | None = None
    description: str | None = None
    mileage_at_service: int | None = None
    cost: Decimal | None = None
    currency: Currency | None = None
    provider: str | None = None


class MaintenanceRecordDeleteInput(MutableDTO):
    organization_id: UUID
    maintenance_record_id: UUID


class MaintenanceScheduleGetInput(MutableDTO):
    organization_id: UUID
    maintenance_schedule_id: UUID


class MaintenanceScheduleListInput(MutableDTO):
    organization_id: UUID
    car_ids: list[UUID] | None = None
    service_types: list[ServiceType] | None = None
    is_completed: bool | None = None
    offset: int = 0
    limit: int | None = None


class MaintenanceScheduleDueByDateInput(MutableDTO):
    organization_id: UUID
    due_date: date


class MaintenanceScheduleDueByMileageInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    mileage: int


class MaintenanceScheduleCreateInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    service_type: ServiceType
    scheduled_date: date | None = None
    scheduled_mileage: int | None = None
    interval_km: int | None = None


class MaintenanceScheduleUpdateInput(MutableDTO):
    organization_id: UUID
    maintenance_schedule_id: UUID
    service_type: ServiceType | None = None
    scheduled_date: date | None = None
    scheduled_mileage: int | None = None
    interval_km: int | None = None


class MaintenanceScheduleCompleteInput(MutableDTO):
    organization_id: UUID
    maintenance_schedule_id: UUID
    maintenance_record_id: UUID


class MaintenanceScheduleDeleteInput(MutableDTO):
    organization_id: UUID
    maintenance_schedule_id: UUID
