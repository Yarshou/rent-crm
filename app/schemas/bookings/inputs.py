from datetime import date
from decimal import Decimal
from uuid import UUID

from db.models import BookingStatus, Currency
from schemas.base import MutableDTO

__all__ = [
    "BookingActivateInput",
    "BookingCancelInput",
    "BookingCompleteInput",
    "BookingCreateInput",
    "BookingDeleteInput",
    "BookingGetInput",
    "BookingListInput",
    "BookingRescheduleInput",
    "BookingTotalInput",
    "BookingUpdateDetailsInput",
]


class BookingGetInput(MutableDTO):
    organization_id: UUID
    booking_id: UUID


class BookingListInput(MutableDTO):
    organization_id: UUID
    car_ids: list[UUID] | None = None
    statuses: list[BookingStatus] | None = None
    date_from: date | None = None
    date_to: date | None = None
    offset: int = 0
    limit: int | None = None


class BookingTotalInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    start_date: date
    end_date: date


class BookingCreateInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    start_date: date
    end_date: date
    renter_name: str
    renter_phone: str
    total_amount: Decimal | None = None
    currency: Currency | None = None
    notes: str | None = None


class BookingUpdateDetailsInput(MutableDTO):
    organization_id: UUID
    booking_id: UUID
    renter_name: str | None = None
    renter_phone: str | None = None
    total_amount: Decimal | None = None
    currency: Currency | None = None
    notes: str | None = None


class BookingRescheduleInput(MutableDTO):
    organization_id: UUID
    booking_id: UUID
    start_date: date
    end_date: date
    car_id: UUID | None = None
    total_amount: Decimal | None = None
    currency: Currency | None = None
    recalculate_total: bool = True


class BookingActivateInput(MutableDTO):
    organization_id: UUID
    booking_id: UUID
    pickup_mileage: int


class BookingCompleteInput(MutableDTO):
    organization_id: UUID
    booking_id: UUID
    return_mileage: int


class BookingCancelInput(MutableDTO):
    organization_id: UUID
    booking_id: UUID


class BookingDeleteInput(MutableDTO):
    organization_id: UUID
    booking_id: UUID
