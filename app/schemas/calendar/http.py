from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field
from schemas.bookings.http import BookingResponse
from schemas.cars.http import CarRepairPeriodResponse, CarResponse

__all__ = ["CalendarResponse", "RepairPeriodResponse"]


class RepairPeriodResponse(BaseModel):
    car_id: UUID
    date_from: date
    date_to: date
    title: str | None = None


class CalendarResponse(BaseModel):
    date_from: date
    date_to: date
    cars: list[CarResponse]
    bookings: list[BookingResponse]
    repair_periods: list[CarRepairPeriodResponse] = Field(default_factory=list)
