from datetime import date
from decimal import Decimal
from uuid import UUID

from repositories import UnitOfWork
from schemas.cars import CarDTO
from schemas.maintenance import (
    MaintenanceRecordCreateInput,
    MaintenanceRecordDeleteInput,
    MaintenanceRecordDTO,
    MaintenanceRecordGetInput,
    MaintenanceRecordListInput,
    MaintenanceRecordUpdateInput,
    MaintenanceScheduleCompleteInput,
    MaintenanceScheduleCreateInput,
    MaintenanceScheduleDeleteInput,
    MaintenanceScheduleDTO,
    MaintenanceScheduleDueByDateInput,
    MaintenanceScheduleDueByMileageInput,
    MaintenanceScheduleGetInput,
    MaintenanceScheduleListInput,
    MaintenanceScheduleUpdateInput,
)

from ..common import ServiceConflictError, ServiceNotFoundError, ServiceValidationError, UnitOfWorkFactory

__all__ = ["MaintenanceService"]


class MaintenanceService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_record(self, input: MaintenanceRecordGetInput) -> MaintenanceRecordDTO:
        async with self._uow_factory() as uow:
            return await self._get_record(
                uow,
                organization_id=input.organization_id,
                maintenance_record_id=input.maintenance_record_id,
            )

    async def list_records(self, input: MaintenanceRecordListInput) -> list[MaintenanceRecordDTO]:
        async with self._uow_factory() as uow:
            return await uow.maintenance_records.list_for_organization(
                input.organization_id,
                car_ids=input.car_ids,
                service_types=input.service_types,
                date_from=input.date_from,
                date_to=input.date_to,
                offset=input.offset,
                limit=input.limit,
            )

    async def create_record(self, input: MaintenanceRecordCreateInput) -> MaintenanceRecordDTO:
        self._validate_mileage(input.mileage_at_service)
        self._validate_cost(input.cost)

        async with self._uow_factory() as uow:
            car = await self._get_car_for_update(uow, organization_id=input.organization_id, car_id=input.car_id)
            self._ensure_mileage_does_not_decrease(input.mileage_at_service, car.mileage)

            record = await uow.maintenance_records.create(
                organization_id=input.organization_id,
                car_id=input.car_id,
                service_date=input.service_date,
                service_type=input.service_type,
                description=input.description,
                mileage_at_service=input.mileage_at_service,
                cost=input.cost,
                provider=input.provider,
            )
            await self._update_car_mileage_if_needed(uow, car=car, mileage=input.mileage_at_service)

            if input.complete_schedule_id is not None:
                schedule = await self._get_schedule(
                    uow,
                    organization_id=input.organization_id,
                    maintenance_schedule_id=input.complete_schedule_id,
                )
                self._ensure_schedule_matches_record(schedule=schedule, record=record)
                await self._complete_schedule(uow, schedule=schedule, record=record)

            await uow.commit()
            return record

    async def update_record(self, input: MaintenanceRecordUpdateInput) -> MaintenanceRecordDTO:
        values = input.model_dump(
            exclude={"organization_id", "maintenance_record_id"},
            exclude_unset=True,
            exclude_none=True,
        )
        if "mileage_at_service" in values:
            self._validate_mileage(values["mileage_at_service"])
        if "cost" in values:
            self._validate_cost(values["cost"])

        async with self._uow_factory() as uow:
            record = await self._get_record(
                uow,
                organization_id=input.organization_id,
                maintenance_record_id=input.maintenance_record_id,
            )
            car = await self._get_car_for_update(uow, organization_id=input.organization_id, car_id=record.car_id)

            if "mileage_at_service" in values:
                self._ensure_mileage_does_not_decrease(values["mileage_at_service"], car.mileage)
                await self._update_car_mileage_if_needed(uow, car=car, mileage=values["mileage_at_service"])

            if not values:
                return record

            updated = await uow.maintenance_records.update(input.maintenance_record_id, **values)
            if updated is None:
                raise ServiceNotFoundError("Maintenance record not found.")
            await uow.commit()
            return updated

    async def delete_record(self, input: MaintenanceRecordDeleteInput) -> None:
        async with self._uow_factory() as uow:
            await self._get_record(
                uow,
                organization_id=input.organization_id,
                maintenance_record_id=input.maintenance_record_id,
            )
            deleted = await uow.maintenance_records.delete_by_id(input.maintenance_record_id)
            if not deleted:
                raise ServiceNotFoundError("Maintenance record not found.")

            await uow.commit()

    async def get_schedule(self, input: MaintenanceScheduleGetInput) -> MaintenanceScheduleDTO:
        async with self._uow_factory() as uow:
            return await self._get_schedule(
                uow,
                organization_id=input.organization_id,
                maintenance_schedule_id=input.maintenance_schedule_id,
            )

    async def list_schedules(self, input: MaintenanceScheduleListInput) -> list[MaintenanceScheduleDTO]:
        async with self._uow_factory() as uow:
            return await uow.maintenance_schedules.list_for_organization(
                input.organization_id,
                car_ids=input.car_ids,
                service_types=input.service_types,
                is_completed=input.is_completed,
                offset=input.offset,
                limit=input.limit,
            )

    async def list_due_by_date(self, input: MaintenanceScheduleDueByDateInput) -> list[MaintenanceScheduleDTO]:
        async with self._uow_factory() as uow:
            return await uow.maintenance_schedules.list_due_by_date(
                organization_id=input.organization_id,
                due_date=input.due_date,
            )

    async def list_due_by_mileage(self, input: MaintenanceScheduleDueByMileageInput) -> list[MaintenanceScheduleDTO]:
        self._validate_mileage(input.mileage)

        async with self._uow_factory() as uow:
            await self._get_car(uow, organization_id=input.organization_id, car_id=input.car_id)
            return await uow.maintenance_schedules.list_due_by_mileage(
                organization_id=input.organization_id,
                car_id=input.car_id,
                mileage=input.mileage,
            )

    async def create_schedule(self, input: MaintenanceScheduleCreateInput) -> MaintenanceScheduleDTO:
        self._validate_schedule_values(
            scheduled_date=input.scheduled_date,
            scheduled_mileage=input.scheduled_mileage,
            interval_km=input.interval_km,
        )

        async with self._uow_factory() as uow:
            car = await self._get_car(uow, organization_id=input.organization_id, car_id=input.car_id)
            if input.scheduled_mileage is not None:
                self._ensure_mileage_does_not_decrease(input.scheduled_mileage, car.mileage)

            schedule = await uow.maintenance_schedules.create(
                organization_id=input.organization_id,
                car_id=input.car_id,
                service_type=input.service_type,
                scheduled_date=input.scheduled_date,
                scheduled_mileage=input.scheduled_mileage,
                interval_km=input.interval_km,
                is_completed=False,
                maintenance_record_id=None,
            )
            await uow.commit()
            return schedule

    async def update_schedule(self, input: MaintenanceScheduleUpdateInput) -> MaintenanceScheduleDTO:
        values = input.model_dump(
            exclude={"organization_id", "maintenance_schedule_id"},
            exclude_unset=True,
        )

        async with self._uow_factory() as uow:
            schedule = await self._get_schedule(
                uow,
                organization_id=input.organization_id,
                maintenance_schedule_id=input.maintenance_schedule_id,
            )
            if schedule.is_completed:
                raise ServiceConflictError("Completed maintenance schedule cannot be changed.")

            scheduled_date = values.get("scheduled_date", schedule.scheduled_date)
            scheduled_mileage = values.get("scheduled_mileage", schedule.scheduled_mileage)
            interval_km = values.get("interval_km", schedule.interval_km)
            self._validate_schedule_values(
                scheduled_date=scheduled_date,
                scheduled_mileage=scheduled_mileage,
                interval_km=interval_km,
            )

            if "scheduled_mileage" in values and scheduled_mileage is not None:
                car = await self._get_car(uow, organization_id=input.organization_id, car_id=schedule.car_id)
                self._ensure_mileage_does_not_decrease(scheduled_mileage, car.mileage)

            if not values:
                return schedule

            updated = await uow.maintenance_schedules.update(input.maintenance_schedule_id, **values)
            if updated is None:
                raise ServiceNotFoundError("Maintenance schedule not found.")
            await uow.commit()
            return updated

    async def complete_schedule(self, input: MaintenanceScheduleCompleteInput) -> MaintenanceScheduleDTO:
        async with self._uow_factory() as uow:
            schedule = await self._get_schedule(
                uow,
                organization_id=input.organization_id,
                maintenance_schedule_id=input.maintenance_schedule_id,
            )
            record = await self._get_record(
                uow,
                organization_id=input.organization_id,
                maintenance_record_id=input.maintenance_record_id,
            )
            self._ensure_schedule_matches_record(schedule=schedule, record=record)
            updated = await self._complete_schedule(uow, schedule=schedule, record=record)
            await uow.commit()
            return updated

    async def delete_schedule(self, input: MaintenanceScheduleDeleteInput) -> None:
        async with self._uow_factory() as uow:
            schedule = await self._get_schedule(
                uow,
                organization_id=input.organization_id,
                maintenance_schedule_id=input.maintenance_schedule_id,
            )
            if schedule.is_completed:
                raise ServiceConflictError("Completed maintenance schedule cannot be deleted.")

            deleted = await uow.maintenance_schedules.delete_by_id(input.maintenance_schedule_id)
            if not deleted:
                raise ServiceNotFoundError("Maintenance schedule not found.")

            await uow.commit()

    async def _get_car(self, uow: UnitOfWork, *, organization_id: UUID, car_id: UUID) -> CarDTO:
        car = await uow.cars.get_for_organization(organization_id=organization_id, car_id=car_id)
        if car is None:
            raise ServiceNotFoundError("Car not found.")
        return car

    async def _get_car_for_update(self, uow: UnitOfWork, *, organization_id: UUID, car_id: UUID) -> CarDTO:
        car = await uow.cars.get_for_organization_for_update(organization_id=organization_id, car_id=car_id)
        if car is None:
            raise ServiceNotFoundError("Car not found.")
        return car

    async def _get_record(
        self,
        uow: UnitOfWork,
        *,
        organization_id: UUID,
        maintenance_record_id: UUID,
    ) -> MaintenanceRecordDTO:
        record = await uow.maintenance_records.get_for_organization(
            organization_id=organization_id,
            maintenance_record_id=maintenance_record_id,
        )
        if record is None:
            raise ServiceNotFoundError("Maintenance record not found.")
        return record

    async def _get_schedule(
        self,
        uow: UnitOfWork,
        *,
        organization_id: UUID,
        maintenance_schedule_id: UUID,
    ) -> MaintenanceScheduleDTO:
        schedule = await uow.maintenance_schedules.get_for_organization(
            organization_id=organization_id,
            maintenance_schedule_id=maintenance_schedule_id,
        )
        if schedule is None:
            raise ServiceNotFoundError("Maintenance schedule not found.")
        return schedule

    async def _complete_schedule(
        self,
        uow: UnitOfWork,
        *,
        schedule: MaintenanceScheduleDTO,
        record: MaintenanceRecordDTO,
    ) -> MaintenanceScheduleDTO:
        if schedule.is_completed:
            raise ServiceConflictError("Maintenance schedule is already completed.")

        updated = await uow.maintenance_schedules.update(
            schedule.id,
            is_completed=True,
            maintenance_record_id=record.id,
        )
        if updated is None:
            raise ServiceNotFoundError("Maintenance schedule not found.")
        if schedule.interval_km is not None:
            await uow.maintenance_schedules.create(
                organization_id=schedule.organization_id,
                car_id=schedule.car_id,
                service_type=schedule.service_type,
                scheduled_date=None,
                scheduled_mileage=record.mileage_at_service + schedule.interval_km,
                interval_km=schedule.interval_km,
                is_completed=False,
                maintenance_record_id=None,
            )
        return updated

    async def _update_car_mileage_if_needed(self, uow: UnitOfWork, *, car: CarDTO, mileage: int) -> None:
        if mileage > car.mileage:
            await uow.cars.update_mileage(car.id, mileage)

    def _ensure_schedule_matches_record(
        self,
        *,
        schedule: MaintenanceScheduleDTO,
        record: MaintenanceRecordDTO,
    ) -> None:
        if schedule.organization_id != record.organization_id or schedule.car_id != record.car_id:
            raise ServiceValidationError("Maintenance record does not belong to the scheduled car.")
        if schedule.service_type != record.service_type:
            raise ServiceValidationError("Maintenance record service type does not match schedule service type.")

    def _validate_schedule_values(
        self,
        *,
        scheduled_date: date | None,
        scheduled_mileage: int | None,
        interval_km: int | None,
    ) -> None:
        if scheduled_date is None and scheduled_mileage is None:
            raise ServiceValidationError("Maintenance schedule requires scheduled_date or scheduled_mileage.")
        if scheduled_mileage is not None:
            self._validate_mileage(scheduled_mileage)
        if interval_km is not None and interval_km <= 0:
            raise ServiceValidationError("Maintenance interval_km must be positive.")

    def _ensure_mileage_does_not_decrease(self, mileage: int, current_mileage: int) -> None:
        if mileage < current_mileage:
            raise ServiceValidationError("Maintenance mileage cannot be lower than current car mileage.")

    def _validate_mileage(self, mileage: int) -> None:
        if mileage < 0:
            raise ServiceValidationError("Maintenance mileage cannot be negative.")

    def _validate_cost(self, cost: Decimal) -> None:
        if cost < 0:
            raise ServiceValidationError("Maintenance cost cannot be negative.")
