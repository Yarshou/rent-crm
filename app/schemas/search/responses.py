from datetime import date
from uuid import UUID

from db.models import BookingStatus, CarStatus
from pydantic import BaseModel

__all__ = [
    "SearchBookingResult",
    "SearchCarResult",
    "SearchClientResult",
    "SearchResponse",
]


class SearchCarResult(BaseModel):
    id: UUID
    brand: str
    model: str
    license_plate: str
    status: CarStatus


class SearchBookingResult(BaseModel):
    id: UUID
    car_id: UUID
    renter_name: str
    renter_phone: str
    status: BookingStatus
    start_date: date
    end_date: date


class SearchClientResult(BaseModel):
    renter_name: str
    renter_phone: str


class SearchResponse(BaseModel):
    cars: list[SearchCarResult]
    bookings: list[SearchBookingResult]
    clients: list[SearchClientResult]
