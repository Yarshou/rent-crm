from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field
from schemas.base.common import BaseEntityResponse

__all__ = ["InsurancePaymentCreateRequest", "InsurancePaymentResponse", "InsurancePaymentUpdateRequest"]


class InsurancePaymentCreateRequest(BaseModel):
    car_id: UUID
    payment_date: date
    period_start: date
    period_end: date
    amount: Decimal = Field(ge=0)
    provider: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class InsurancePaymentUpdateRequest(BaseModel):
    payment_date: date = None
    period_start: date = None
    period_end: date = None
    amount: Decimal = Field(default=None, ge=0)
    provider: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class InsurancePaymentResponse(BaseEntityResponse):
    organization_id: UUID
    car_id: UUID
    payment_date: date
    period_start: date
    period_end: date
    amount: Decimal
    provider: str | None
    notes: str | None
