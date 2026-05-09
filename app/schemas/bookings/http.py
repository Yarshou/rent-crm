from datetime import date
from decimal import Decimal
from uuid import UUID

from db.models import BookingStatus, Currency
from pydantic import BaseModel, Field
from schemas.base.common import BaseEntityResponse

__all__ = [
    "BookingActivateRequest",
    "BookingCompleteRequest",
    "BookingCreateRequest",
    "BookingRescheduleRequest",
    "BookingResponse",
    "BookingTotalRequest",
    "BookingUpdateDetailsRequest",
]


class BookingCreateRequest(BaseModel):
    car_id: UUID
    start_date: date
    end_date: date
    renter_name: str = Field(min_length=1, max_length=255)
    renter_phone: str = Field(min_length=1, max_length=32)
    total_amount: Decimal | None = Field(default=None, ge=0)
    currency: Currency | None = None
    notes: str | None = None


class BookingUpdateDetailsRequest(BaseModel):
    renter_name: str = Field(default=None, min_length=1, max_length=255)
    renter_phone: str = Field(default=None, min_length=1, max_length=32)
    total_amount: Decimal = Field(default=None, ge=0)
    currency: Currency | None = None
    notes: str | None = None


class BookingRescheduleRequest(BaseModel):
    start_date: date
    end_date: date
    car_id: UUID | None = None
    total_amount: Decimal | None = Field(default=None, ge=0)
    currency: Currency | None = None
    recalculate_total: bool = True


class BookingActivateRequest(BaseModel):
    pickup_mileage: int = Field(ge=0)


class BookingCompleteRequest(BaseModel):
    return_mileage: int = Field(ge=0)


class BookingTotalRequest(BaseModel):
    car_id: UUID
    start_date: date
    end_date: date


class BookingResponse(BaseEntityResponse):
    organization_id: UUID
    car_id: UUID
    start_date: date
    end_date: date
    renter_name: str
    renter_phone: str
    total_amount: Decimal
    currency: Currency
    pickup_mileage: int | None
    return_mileage: int | None
    status: BookingStatus
    notes: str | None
