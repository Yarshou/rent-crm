from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from repositories import UnitOfWork
from schemas.insurance import (
    InsurancePaymentActiveOnDateInput,
    InsurancePaymentCreateInput,
    InsurancePaymentDeleteInput,
    InsurancePaymentDTO,
    InsurancePaymentGetInput,
    InsurancePaymentListForCarInput,
    InsurancePaymentListInput,
    InsurancePaymentUpdateInput,
)

from ..common import ServiceNotFoundError, ServiceValidationError, UnitOfWorkFactory

__all__ = ["InsuranceService"]


class InsuranceService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get(self, input: InsurancePaymentGetInput) -> InsurancePaymentDTO:
        async with self._uow_factory() as uow:
            payment = await uow.insurance_payments.get_for_organization(
                organization_id=input.organization_id,
                insurance_payment_id=input.insurance_payment_id,
            )
            if payment is None:
                raise ServiceNotFoundError("Insurance payment not found.")
            return payment

    async def list(self, input: InsurancePaymentListInput) -> list[InsurancePaymentDTO]:
        async with self._uow_factory() as uow:
            return await uow.insurance_payments.list_for_organization(
                input.organization_id,
                car_ids=input.car_ids,
                payment_date_from=input.payment_date_from,
                payment_date_to=input.payment_date_to,
                coverage_from=input.coverage_from,
                coverage_to=input.coverage_to,
                offset=input.offset,
                limit=input.limit,
            )

    async def list_for_car(self, input: InsurancePaymentListForCarInput) -> list[InsurancePaymentDTO]:
        async with self._uow_factory() as uow:
            await self._ensure_car_exists(uow, organization_id=input.organization_id, car_id=input.car_id)
            return await uow.insurance_payments.list_for_car(
                organization_id=input.organization_id,
                car_id=input.car_id,
                coverage_from=input.coverage_from,
                coverage_to=input.coverage_to,
            )

    async def list_active_on_date(self, input: InsurancePaymentActiveOnDateInput) -> list[InsurancePaymentDTO]:
        async with self._uow_factory() as uow:
            return await uow.insurance_payments.list_active_on_date(
                organization_id=input.organization_id,
                target_date=input.target_date,
            )

    async def create(self, input: InsurancePaymentCreateInput) -> InsurancePaymentDTO:
        self._validate_period(period_start=input.period_start, period_end=input.period_end)
        self._validate_amount(input.amount)

        async with self._uow_factory() as uow:
            await self._ensure_car_exists(uow, organization_id=input.organization_id, car_id=input.car_id)
            payment = await uow.insurance_payments.create(
                organization_id=input.organization_id,
                car_id=input.car_id,
                payment_date=input.payment_date,
                period_start=input.period_start,
                period_end=input.period_end,
                amount=input.amount,
                provider=input.provider,
                notes=input.notes,
            )
            await uow.commit()
            return payment

    async def update(self, input: InsurancePaymentUpdateInput) -> InsurancePaymentDTO:
        values = input.model_dump(
            exclude={"organization_id", "insurance_payment_id"},
            exclude_unset=True,
        )
        if "amount" in values and values["amount"] is not None:
            self._validate_amount(values["amount"])

        async with self._uow_factory() as uow:
            payment = await uow.insurance_payments.get_for_organization(
                organization_id=input.organization_id,
                insurance_payment_id=input.insurance_payment_id,
            )
            if payment is None:
                raise ServiceNotFoundError("Insurance payment not found.")

            period_start = values.get("period_start", payment.period_start)
            period_end = values.get("period_end", payment.period_end)
            self._validate_period(period_start=period_start, period_end=period_end)

            if not values:
                return payment

            updated = await uow.insurance_payments.update(input.insurance_payment_id, **values)
            if updated is None:
                raise ServiceNotFoundError("Insurance payment not found.")
            await uow.commit()
            return updated

    async def delete(self, input: InsurancePaymentDeleteInput) -> None:
        async with self._uow_factory() as uow:
            payment = await uow.insurance_payments.get_for_organization(
                organization_id=input.organization_id,
                insurance_payment_id=input.insurance_payment_id,
            )
            if payment is None:
                raise ServiceNotFoundError("Insurance payment not found.")

            deleted = await uow.insurance_payments.delete_by_id(input.insurance_payment_id)
            if not deleted:
                raise ServiceNotFoundError("Insurance payment not found.")

            await uow.commit()

    async def _ensure_car_exists(self, uow: UnitOfWork, *, organization_id: UUID, car_id: UUID) -> None:
        car = await uow.cars.get_for_organization(organization_id=organization_id, car_id=car_id)
        if car is None:
            raise ServiceNotFoundError("Car not found.")

    def _validate_period(self, *, period_start: date, period_end: date) -> None:
        if period_end < period_start:
            raise ServiceValidationError("Insurance coverage end date cannot be earlier than start date.")

    def _validate_amount(self, amount: Decimal) -> None:
        if amount < 0:
            raise ServiceValidationError("Insurance payment amount cannot be negative.")
