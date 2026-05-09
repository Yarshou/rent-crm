from datetime import date
from decimal import Decimal
from uuid import UUID

from db.models import Currency
from schemas.base import MutableDTO

__all__ = [
    "InsurancePaymentActiveOnDateInput",
    "InsurancePaymentCreateInput",
    "InsurancePaymentDeleteInput",
    "InsurancePaymentGetInput",
    "InsurancePaymentListForCarInput",
    "InsurancePaymentListInput",
    "InsurancePaymentUpdateInput",
]


class InsurancePaymentGetInput(MutableDTO):
    organization_id: UUID
    insurance_payment_id: UUID


class InsurancePaymentListInput(MutableDTO):
    organization_id: UUID
    car_ids: list[UUID] | None = None
    payment_date_from: date | None = None
    payment_date_to: date | None = None
    coverage_from: date | None = None
    coverage_to: date | None = None
    offset: int = 0
    limit: int | None = None


class InsurancePaymentListForCarInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    coverage_from: date | None = None
    coverage_to: date | None = None


class InsurancePaymentActiveOnDateInput(MutableDTO):
    organization_id: UUID
    target_date: date


class InsurancePaymentCreateInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    payment_date: date
    period_start: date
    period_end: date
    amount: Decimal
    currency: Currency
    provider: str | None = None
    notes: str | None = None


class InsurancePaymentUpdateInput(MutableDTO):
    organization_id: UUID
    insurance_payment_id: UUID
    payment_date: date | None = None
    period_start: date | None = None
    period_end: date | None = None
    amount: Decimal | None = None
    currency: Currency | None = None
    provider: str | None = None
    notes: str | None = None


class InsurancePaymentDeleteInput(MutableDTO):
    organization_id: UUID
    insurance_payment_id: UUID
