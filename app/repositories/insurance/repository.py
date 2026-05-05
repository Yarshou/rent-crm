from datetime import date
from uuid import UUID

from db.models import InsurancePayment
from repositories import BaseRepository
from schemas.insurance import InsurancePaymentDTO
from sqlalchemy import select

__all__ = ["InsurancePaymentRepository"]


class InsurancePaymentRepository(BaseRepository[InsurancePayment, InsurancePaymentDTO]):
    model = InsurancePayment
    dto = InsurancePaymentDTO

    async def get_for_organization(
        self,
        *,
        organization_id: UUID,
        insurance_payment_id: UUID,
    ) -> InsurancePaymentDTO | None:
        result = await self.session.execute(
            select(InsurancePayment).where(
                InsurancePayment.id == insurance_payment_id,
                InsurancePayment.organization_id == organization_id,
            ),
        )
        instance = result.scalar_one_or_none()
        return self._to_dto(instance) if instance is not None else None

    async def list_for_organization(
        self,
        organization_id: UUID,
        *,
        car_ids: list[UUID] | None = None,
        payment_date_from: date | None = None,
        payment_date_to: date | None = None,
        coverage_from: date | None = None,
        coverage_to: date | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[InsurancePaymentDTO]:
        statement = (
            select(InsurancePayment)
            .where(InsurancePayment.organization_id == organization_id)
            .order_by(InsurancePayment.payment_date.desc(), InsurancePayment.created_at.desc())
            .offset(offset)
        )

        if car_ids:
            statement = statement.where(InsurancePayment.car_id.in_(car_ids))
        if payment_date_from is not None:
            statement = statement.where(InsurancePayment.payment_date >= payment_date_from)
        if payment_date_to is not None:
            statement = statement.where(InsurancePayment.payment_date <= payment_date_to)
        if coverage_from is not None:
            statement = statement.where(InsurancePayment.period_end >= coverage_from)
        if coverage_to is not None:
            statement = statement.where(InsurancePayment.period_start <= coverage_to)
        if limit is not None:
            statement = statement.limit(limit)

        result = await self.session.execute(statement)
        return self._to_dtos(result.scalars().all())

    async def list_for_car(
        self,
        *,
        organization_id: UUID,
        car_id: UUID,
        coverage_from: date | None = None,
        coverage_to: date | None = None,
    ) -> list[InsurancePaymentDTO]:
        return await self.list_for_organization(
            organization_id,
            car_ids=[car_id],
            coverage_from=coverage_from,
            coverage_to=coverage_to,
        )

    async def list_active_on_date(self, *, organization_id: UUID, target_date: date) -> list[InsurancePaymentDTO]:
        result = await self.session.execute(
            select(InsurancePayment)
            .where(
                InsurancePayment.organization_id == organization_id,
                InsurancePayment.period_start <= target_date,
                InsurancePayment.period_end >= target_date,
            )
            .order_by(InsurancePayment.period_end, InsurancePayment.payment_date),
        )
        return self._to_dtos(result.scalars().all())
