from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from db.models import BookingStatus, CarStatus
from repositories import UnitOfWork
from schemas.bookings import (
    BookingActivateInput,
    BookingCancelInput,
    BookingCompleteInput,
    BookingCreateInput,
    BookingDeleteInput,
    BookingDTO,
    BookingGetInput,
    BookingListInput,
    BookingRescheduleInput,
    BookingTotalInput,
    BookingUpdateDetailsInput,
)
from schemas.cars import CarDTO

from ..common import ServiceConflictError, ServiceNotFoundError, ServiceValidationError, UnitOfWorkFactory

__all__ = ["BookingService"]


class BookingService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get(self, input: BookingGetInput) -> BookingDTO:
        async with self._uow_factory() as uow:
            return await self._get_booking(
                uow,
                organization_id=input.organization_id,
                booking_id=input.booking_id,
            )

    async def list(self, input: BookingListInput) -> list[BookingDTO]:
        async with self._uow_factory() as uow:
            return await uow.bookings.list_for_organization(
                input.organization_id,
                car_ids=input.car_ids,
                statuses=input.statuses,
                date_from=input.date_from,
                date_to=input.date_to,
                offset=input.offset,
                limit=input.limit,
            )

    async def calculate_total_amount(self, input: BookingTotalInput) -> Decimal:
        self._validate_dates(start_date=input.start_date, end_date=input.end_date)

        async with self._uow_factory() as uow:
            await self._get_car(uow, organization_id=input.organization_id, car_id=input.car_id)
            return await self._calculate_total_amount(
                uow,
                car_id=input.car_id,
                start_date=input.start_date,
                end_date=input.end_date,
            )

    async def create(self, input: BookingCreateInput) -> BookingDTO:
        self._validate_dates(start_date=input.start_date, end_date=input.end_date)
        self._validate_amount(input.total_amount)

        async with self._uow_factory() as uow:
            car = await self._get_car_for_update(uow, organization_id=input.organization_id, car_id=input.car_id)
            self._ensure_car_can_accept_booking(car)
            await self._ensure_no_overlap(
                uow,
                organization_id=input.organization_id,
                car_id=input.car_id,
                start_date=input.start_date,
                end_date=input.end_date,
            )

            amount = input.total_amount
            if amount is None:
                amount = await self._calculate_total_amount(
                    uow,
                    car_id=input.car_id,
                    start_date=input.start_date,
                    end_date=input.end_date,
                )

            booking = await uow.bookings.create(
                organization_id=input.organization_id,
                car_id=input.car_id,
                start_date=input.start_date,
                end_date=input.end_date,
                renter_name=input.renter_name,
                renter_phone=input.renter_phone,
                total_amount=amount,
                pickup_mileage=None,
                return_mileage=None,
                status=BookingStatus.planned,
                notes=input.notes,
            )
            await uow.commit()
            return booking

    async def update_details(self, input: BookingUpdateDetailsInput) -> BookingDTO:
        values = input.model_dump(exclude={"organization_id", "booking_id"}, exclude_unset=True, exclude_none=True)
        if "total_amount" in values:
            self._validate_amount(values["total_amount"])

        async with self._uow_factory() as uow:
            booking = await self._get_booking_for_update(
                uow,
                organization_id=input.organization_id,
                booking_id=input.booking_id,
            )
            if booking.status in {BookingStatus.completed, BookingStatus.cancelled}:
                raise ServiceConflictError("Completed or cancelled booking details cannot be changed.")

            if not values:
                return booking

            updated = await uow.bookings.update(input.booking_id, **values)
            if updated is None:
                raise ServiceNotFoundError("Booking not found.")
            await uow.commit()
            return updated

    async def reschedule(self, input: BookingRescheduleInput) -> BookingDTO:
        self._validate_dates(start_date=input.start_date, end_date=input.end_date)
        self._validate_amount(input.total_amount)

        async with self._uow_factory() as uow:
            booking = await self._get_booking_for_update(
                uow,
                organization_id=input.organization_id,
                booking_id=input.booking_id,
            )
            if booking.status in {BookingStatus.completed, BookingStatus.cancelled}:
                raise ServiceConflictError("Completed or cancelled booking cannot be rescheduled.")

            target_car_id = input.car_id or booking.car_id
            if booking.status == BookingStatus.active and target_car_id != booking.car_id:
                raise ServiceConflictError("Active booking cannot be moved to another car.")

            car = await self._get_car_for_update(uow, organization_id=input.organization_id, car_id=target_car_id)
            if target_car_id != booking.car_id or booking.status != BookingStatus.active:
                self._ensure_car_can_accept_booking(car)

            await self._ensure_no_overlap(
                uow,
                organization_id=input.organization_id,
                car_id=target_car_id,
                start_date=input.start_date,
                end_date=input.end_date,
                exclude_booking_id=booking.id,
            )

            values: dict[str, object] = {
                "car_id": target_car_id,
                "start_date": input.start_date,
                "end_date": input.end_date,
            }
            if input.total_amount is not None:
                values["total_amount"] = input.total_amount
            elif input.recalculate_total:
                values["total_amount"] = await self._calculate_total_amount(
                    uow,
                    car_id=target_car_id,
                    start_date=input.start_date,
                    end_date=input.end_date,
                )

            updated = await uow.bookings.update(booking.id, **values)
            if updated is None:
                raise ServiceNotFoundError("Booking not found.")
            await uow.commit()
            return updated

    async def activate(self, input: BookingActivateInput) -> BookingDTO:
        self._validate_mileage(input.pickup_mileage)

        async with self._uow_factory() as uow:
            booking = await self._get_booking_for_update(
                uow,
                organization_id=input.organization_id,
                booking_id=input.booking_id,
            )
            if booking.status != BookingStatus.planned:
                raise ServiceConflictError("Only planned bookings can be activated.")

            car = await self._get_car_for_update(uow, organization_id=input.organization_id, car_id=booking.car_id)
            self._ensure_car_can_accept_booking(car)
            active_count = await uow.bookings.count_active_for_car(
                organization_id=input.organization_id,
                car_id=booking.car_id,
            )
            if active_count > 0:
                raise ServiceConflictError("Car already has an active booking.")
            if input.pickup_mileage < car.mileage:
                raise ServiceValidationError("Pickup mileage cannot be lower than current car mileage.")

            await self._ensure_no_overlap(
                uow,
                organization_id=input.organization_id,
                car_id=booking.car_id,
                start_date=booking.start_date,
                end_date=booking.end_date,
                exclude_booking_id=booking.id,
            )

            updated = await uow.bookings.update(
                booking.id,
                pickup_mileage=input.pickup_mileage,
                status=BookingStatus.active,
            )
            if updated is None:
                raise ServiceNotFoundError("Booking not found.")
            await uow.cars.set_status(car.id, CarStatus.rented)
            await uow.commit()
            return updated

    async def complete(self, input: BookingCompleteInput) -> BookingDTO:
        self._validate_mileage(input.return_mileage)

        async with self._uow_factory() as uow:
            booking = await self._get_booking_for_update(
                uow,
                organization_id=input.organization_id,
                booking_id=input.booking_id,
            )
            if booking.status != BookingStatus.active:
                raise ServiceConflictError("Only active bookings can be completed.")
            if booking.pickup_mileage is None:
                raise ServiceValidationError("Active booking has no pickup mileage.")

            car = await self._get_car_for_update(uow, organization_id=input.organization_id, car_id=booking.car_id)
            if input.return_mileage < booking.pickup_mileage:
                raise ServiceValidationError("Return mileage cannot be lower than pickup mileage.")
            if input.return_mileage < car.mileage:
                raise ServiceValidationError("Return mileage cannot be lower than current car mileage.")

            updated = await uow.bookings.update(
                booking.id,
                return_mileage=input.return_mileage,
                status=BookingStatus.completed,
            )
            if updated is None:
                raise ServiceNotFoundError("Booking not found.")
            await uow.cars.update_mileage(car.id, input.return_mileage)
            await self._mark_car_available_if_no_active_bookings(
                uow,
                organization_id=input.organization_id,
                car_id=car.id,
            )
            await uow.commit()
            return updated

    async def cancel(self, input: BookingCancelInput) -> BookingDTO:
        async with self._uow_factory() as uow:
            booking = await self._get_booking_for_update(
                uow,
                organization_id=input.organization_id,
                booking_id=input.booking_id,
            )
            if booking.status == BookingStatus.completed:
                raise ServiceConflictError("Completed booking cannot be cancelled.")
            if booking.status == BookingStatus.cancelled:
                return booking

            was_active = booking.status == BookingStatus.active
            updated = await uow.bookings.update(booking.id, status=BookingStatus.cancelled)
            if updated is None:
                raise ServiceNotFoundError("Booking not found.")

            if was_active:
                await self._mark_car_available_if_no_active_bookings(
                    uow,
                    organization_id=input.organization_id,
                    car_id=booking.car_id,
                )

            await uow.commit()
            return updated

    async def delete(self, input: BookingDeleteInput) -> None:
        async with self._uow_factory() as uow:
            booking = await self._get_booking_for_update(
                uow,
                organization_id=input.organization_id,
                booking_id=input.booking_id,
            )
            if booking.status == BookingStatus.active:
                raise ServiceConflictError("Active booking cannot be deleted.")

            deleted = await uow.bookings.delete_by_id(input.booking_id)
            if not deleted:
                raise ServiceNotFoundError("Booking not found.")

            await uow.commit()

    async def _get_booking(self, uow: UnitOfWork, *, organization_id: UUID, booking_id: UUID) -> BookingDTO:
        booking = await uow.bookings.get_for_organization(organization_id=organization_id, booking_id=booking_id)
        if booking is None:
            raise ServiceNotFoundError("Booking not found.")
        return booking

    async def _get_booking_for_update(self, uow: UnitOfWork, *, organization_id: UUID, booking_id: UUID) -> BookingDTO:
        booking = await uow.bookings.get_for_organization_for_update(
            organization_id=organization_id,
            booking_id=booking_id,
        )
        if booking is None:
            raise ServiceNotFoundError("Booking not found.")
        return booking

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

    async def _calculate_total_amount(
        self,
        uow: UnitOfWork,
        *,
        car_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        rental_days = self._rental_days(start_date=start_date, end_date=end_date)
        tier = await uow.car_pricing_tiers.get_applicable_for_duration(car_id=car_id, rental_days=rental_days)
        if tier is None:
            raise ServiceValidationError("No pricing tier is configured for this booking duration.")
        return tier.daily_rate * rental_days

    async def _ensure_no_overlap(
        self,
        uow: UnitOfWork,
        *,
        organization_id: UUID,
        car_id: UUID,
        start_date: date,
        end_date: date,
        exclude_booking_id: UUID | None = None,
    ) -> None:
        has_overlap = await uow.bookings.has_overlapping_booking(
            organization_id=organization_id,
            car_id=car_id,
            start_date=start_date,
            end_date=end_date,
            exclude_booking_id=exclude_booking_id,
        )
        if has_overlap:
            raise ServiceConflictError("Booking dates overlap with another planned or active booking.")

    async def _mark_car_available_if_no_active_bookings(
        self,
        uow: UnitOfWork,
        *,
        organization_id: UUID,
        car_id: UUID,
    ) -> None:
        active_count = await uow.bookings.count_active_for_car(organization_id=organization_id, car_id=car_id)
        if active_count == 0:
            await uow.cars.set_status(car_id, CarStatus.available)

    def _ensure_car_can_accept_booking(self, car: CarDTO) -> None:
        if car.status == CarStatus.in_repair:
            raise ServiceConflictError("Car is in repair and cannot be booked.")

    def _validate_dates(self, *, start_date: date, end_date: date) -> None:
        if end_date < start_date:
            raise ServiceValidationError("Booking end date cannot be earlier than start date.")

    def _validate_amount(self, amount: Decimal | None) -> None:
        if amount is not None and amount < 0:
            raise ServiceValidationError("Booking amount cannot be negative.")

    def _validate_mileage(self, mileage: int) -> None:
        if mileage < 0:
            raise ServiceValidationError("Booking mileage cannot be negative.")

    def _rental_days(self, *, start_date: date, end_date: date) -> int:
        return (end_date - start_date).days + 1
