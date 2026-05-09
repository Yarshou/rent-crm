from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from db.models import Currency
from schemas.base import ImmutableDTO

__all__ = ["InsurancePaymentDTO"]


class InsurancePaymentDTO(ImmutableDTO):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    organization_id: UUID
    car_id: UUID
    payment_date: date
    period_start: date
    period_end: date
    amount: Decimal
    currency: Currency
    provider: str | None = None
    notes: str | None = None
