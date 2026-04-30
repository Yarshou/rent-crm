from datetime import date
from uuid import UUID

from db.models import Booking, BookingStatus
from repositories import BaseRepository
from sqlalchemy import func, select

__all__ = ["BookingRepository"]

BLOCKING_BOOKING_STATUSES = [BookingStatus.planned, BookingStatus.active]


class BookingRepository(BaseRepository[Booking]):
    model = Booking

    async def get_for_organization(self, *, organization_id: UUID, booking_id: UUID) -> Booking | None:
        result = await self.session.execute(
            select(Booking).where(
                Booking.id == booking_id,
                Booking.organization_id == organization_id,
            ),
        )
        return result.scalar_one_or_none()

    async def get_for_organization_for_update(self, *, organization_id: UUID, booking_id: UUID) -> Booking | None:
        result = await self.session.execute(
            select(Booking)
            .where(
                Booking.id == booking_id,
                Booking.organization_id == organization_id,
            )
            .with_for_update(),
        )
        return result.scalar_one_or_none()

    async def list_for_organization(
        self,
        organization_id: UUID,
        *,
        car_ids: list[UUID] | None = None,
        statuses: list[BookingStatus] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[Booking]:
        statement = (
            select(Booking)
            .where(Booking.organization_id == organization_id)
            .order_by(Booking.start_date, Booking.end_date, Booking.created_at)
            .offset(offset)
        )

        if car_ids:
            statement = statement.where(Booking.car_id.in_(car_ids))
        if statuses:
            statement = statement.where(Booking.status.in_(statuses))
        if date_from is not None:
            statement = statement.where(Booking.end_date >= date_from)
        if date_to is not None:
            statement = statement.where(Booking.start_date <= date_to)
        if limit is not None:
            statement = statement.limit(limit)

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_for_car(
        self,
        *,
        organization_id: UUID,
        car_id: UUID,
        statuses: list[BookingStatus] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Booking]:
        return await self.list_for_organization(
            organization_id,
            car_ids=[car_id],
            statuses=statuses,
            date_from=date_from,
            date_to=date_to,
        )

    async def list_active_for_car(self, *, organization_id: UUID, car_id: UUID) -> list[Booking]:
        return await self.list_for_car(
            organization_id=organization_id,
            car_id=car_id,
            statuses=[BookingStatus.active],
        )

    async def find_overlapping(
        self,
        *,
        organization_id: UUID,
        car_id: UUID,
        start_date: date,
        end_date: date,
        statuses: list[BookingStatus] | None = None,
        exclude_booking_id: UUID | None = None,
    ) -> list[Booking]:
        statement = select(Booking).where(
            Booking.organization_id == organization_id,
            Booking.car_id == car_id,
            Booking.start_date <= end_date,
            Booking.end_date >= start_date,
            Booking.status.in_(statuses or BLOCKING_BOOKING_STATUSES),
        )

        if exclude_booking_id is not None:
            statement = statement.where(Booking.id != exclude_booking_id)

        result = await self.session.execute(statement.order_by(Booking.start_date, Booking.end_date))
        return list(result.scalars().all())

    async def has_overlapping_booking(
        self,
        *,
        organization_id: UUID,
        car_id: UUID,
        start_date: date,
        end_date: date,
        statuses: list[BookingStatus] | None = None,
        exclude_booking_id: UUID | None = None,
    ) -> bool:
        statement = select(Booking.id).where(
            Booking.organization_id == organization_id,
            Booking.car_id == car_id,
            Booking.start_date <= end_date,
            Booking.end_date >= start_date,
            Booking.status.in_(statuses or BLOCKING_BOOKING_STATUSES),
        )

        if exclude_booking_id is not None:
            statement = statement.where(Booking.id != exclude_booking_id)

        result = await self.session.execute(statement.limit(1))
        return result.scalar_one_or_none() is not None

    async def count_active_for_car(self, *, organization_id: UUID, car_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count(Booking.id)).where(
                Booking.organization_id == organization_id,
                Booking.car_id == car_id,
                Booking.status == BookingStatus.active,
            ),
        )
        return result.scalar_one()
