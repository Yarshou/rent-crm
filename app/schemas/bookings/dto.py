from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from db.models import BookingStatus
from schemas.base import ImmutableDTO

__all__ = ["BookingDTO"]


class BookingDTO(ImmutableDTO):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    organization_id: UUID
    car_id: UUID
    start_date: date
    end_date: date
    renter_name: str
    renter_phone: str
    total_amount: Decimal
    pickup_mileage: int | None = None
    return_mileage: int | None = None
    status: BookingStatus
    notes: str | None = None
