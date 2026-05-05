from __future__ import annotations

from uuid import UUID

from schemas.search import (
    SearchBookingResult,
    SearchCarResult,
    SearchClientResult,
    SearchInput,
    SearchResponse,
)

from ..common import UnitOfWorkFactory

__all__ = ["SearchService"]


class SearchService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def search(self, input: SearchInput) -> SearchResponse:
        query = input.q.strip()

        async with self._uow_factory() as uow:
            cars = await uow.cars.search_for_organization(
                input.organization_id,
                query,
                limit=input.limit,
            )

            booking = None
            try:
                booking = await uow.bookings.get_for_organization(
                    organization_id=input.organization_id,
                    booking_id=UUID(query),
                )
            except ValueError:
                pass

            clients = await uow.bookings.search_clients_for_organization(
                input.organization_id,
                query,
                limit=input.limit,
            )

        return SearchResponse(
            cars=[
                SearchCarResult(
                    id=car.id,
                    brand=car.brand,
                    model=car.model,
                    license_plate=car.license_plate,
                    status=car.status,
                )
                for car in cars
            ],
            bookings=[
                SearchBookingResult(
                    id=booking.id,
                    car_id=booking.car_id,
                    renter_name=booking.renter_name,
                    renter_phone=booking.renter_phone,
                    status=booking.status,
                    start_date=booking.start_date,
                    end_date=booking.end_date,
                )
            ]
            if booking
            else [],
            clients=[
                SearchClientResult(renter_name=name, renter_phone=phone)
                for name, phone in clients
            ],
        )
