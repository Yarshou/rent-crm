from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field
from schemas.bookings.http import BookingResponse
from schemas.cars.http import CarResponse

__all__ = ["CalendarResponse", "RepairPeriodResponse"]


class RepairPeriodResponse(BaseModel):
    car_id: UUID
    date_from: date
    date_to: date
    title: str


class CalendarResponse(BaseModel):
    date_from: date
    date_to: date
    cars: list[CarResponse]
    bookings: list[BookingResponse]
    repair_periods: list[RepairPeriodResponse] = Field(default_factory=list)
