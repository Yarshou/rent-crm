from datetime import date
from uuid import UUID

from db.models import MaintenanceRecord, MaintenanceSchedule, ServiceType
from repositories import BaseRepository
from sqlalchemy import select

__all__ = ["MaintenanceRecordRepository", "MaintenanceScheduleRepository"]


class MaintenanceRecordRepository(BaseRepository[MaintenanceRecord]):
    model = MaintenanceRecord

    async def get_for_organization(self, *, organization_id: UUID, maintenance_record_id: UUID) -> MaintenanceRecord | None:
        result = await self.session.execute(
            select(MaintenanceRecord).where(
                MaintenanceRecord.id == maintenance_record_id,
                MaintenanceRecord.organization_id == organization_id,
            ),
        )
        return result.scalar_one_or_none()

    async def list_for_organization(
        self,
        organization_id: UUID,
        *,
        car_ids: list[UUID] | None = None,
        service_types: list[ServiceType] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[MaintenanceRecord]:
        statement = (
            select(MaintenanceRecord)
            .where(MaintenanceRecord.organization_id == organization_id)
            .order_by(MaintenanceRecord.service_date.desc(), MaintenanceRecord.created_at.desc())
            .offset(offset)
        )

        if car_ids:
            statement = statement.where(MaintenanceRecord.car_id.in_(car_ids))
        if service_types:
            statement = statement.where(MaintenanceRecord.service_type.in_(service_types))
        if date_from is not None:
            statement = statement.where(MaintenanceRecord.service_date >= date_from)
        if date_to is not None:
            statement = statement.where(MaintenanceRecord.service_date <= date_to)
        if limit is not None:
            statement = statement.limit(limit)

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_for_car(
        self,
        *,
        organization_id: UUID,
        car_id: UUID,
        service_types: list[ServiceType] | None = None,
    ) -> list[MaintenanceRecord]:
        return await self.list_for_organization(
            organization_id,
            car_ids=[car_id],
            service_types=service_types,
        )


class MaintenanceScheduleRepository(BaseRepository[MaintenanceSchedule]):
    model = MaintenanceSchedule

    async def get_for_organization(
        self,
        *,
        organization_id: UUID,
        maintenance_schedule_id: UUID,
    ) -> MaintenanceSchedule | None:
        result = await self.session.execute(
            select(MaintenanceSchedule).where(
                MaintenanceSchedule.id == maintenance_schedule_id,
                MaintenanceSchedule.organization_id == organization_id,
            ),
        )
        return result.scalar_one_or_none()

    async def list_for_organization(
        self,
        organization_id: UUID,
        *,
        car_ids: list[UUID] | None = None,
        service_types: list[ServiceType] | None = None,
        is_completed: bool | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[MaintenanceSchedule]:
        statement = (
            select(MaintenanceSchedule)
            .where(MaintenanceSchedule.organization_id == organization_id)
            .order_by(
                MaintenanceSchedule.is_completed,
                MaintenanceSchedule.scheduled_date,
                MaintenanceSchedule.scheduled_mileage,
                MaintenanceSchedule.created_at,
            )
            .offset(offset)
        )

        if car_ids:
            statement = statement.where(MaintenanceSchedule.car_id.in_(car_ids))
        if service_types:
            statement = statement.where(MaintenanceSchedule.service_type.in_(service_types))
        if is_completed is not None:
            statement = statement.where(MaintenanceSchedule.is_completed == is_completed)
        if limit is not None:
            statement = statement.limit(limit)

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_open_for_car(self, *, organization_id: UUID, car_id: UUID) -> list[MaintenanceSchedule]:
        return await self.list_for_organization(
            organization_id,
            car_ids=[car_id],
            is_completed=False,
        )

    async def list_due_by_date(self, *, organization_id: UUID, due_date: date) -> list[MaintenanceSchedule]:
        result = await self.session.execute(
            select(MaintenanceSchedule)
            .where(
                MaintenanceSchedule.organization_id == organization_id,
                MaintenanceSchedule.is_completed.is_(False),
                MaintenanceSchedule.scheduled_date.is_not(None),
                MaintenanceSchedule.scheduled_date <= due_date,
            )
            .order_by(MaintenanceSchedule.scheduled_date, MaintenanceSchedule.created_at),
        )
        return list(result.scalars().all())

    async def list_due_by_mileage(
        self,
        *,
        organization_id: UUID,
        car_id: UUID,
        mileage: int,
    ) -> list[MaintenanceSchedule]:
        result = await self.session.execute(
            select(MaintenanceSchedule)
            .where(
                MaintenanceSchedule.organization_id == organization_id,
                MaintenanceSchedule.car_id == car_id,
                MaintenanceSchedule.is_completed.is_(False),
                MaintenanceSchedule.scheduled_mileage.is_not(None),
                MaintenanceSchedule.scheduled_mileage <= mileage,
            )
            .order_by(MaintenanceSchedule.scheduled_mileage, MaintenanceSchedule.created_at),
        )
        return list(result.scalars().all())
