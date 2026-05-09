from decimal import Decimal
from uuid import UUID

from datetime import date

from db.models import Car, CarPhoto, CarPricingTier, CarRepairPeriod, CarStatus
from repositories import BaseRepository
from schemas.cars import CarDTO, CarPhotoDTO, CarPricingTierDTO, CarRepairPeriodDTO
from sqlalchemy import delete, desc, func, or_, select

__all__ = ["CarPhotoRepository", "CarPricingTierRepository", "CarRepairPeriodRepository", "CarRepository"]


class CarRepository(BaseRepository[Car, CarDTO]):
    model = Car
    dto = CarDTO

    async def get_for_organization(self, *, organization_id: UUID, car_id: UUID) -> CarDTO | None:
        result = await self.session.execute(
            select(Car).where(
                Car.id == car_id,
                Car.organization_id == organization_id,
            ),
        )
        instance = result.scalar_one_or_none()
        return self._to_dto(instance) if instance is not None else None

    async def get_for_organization_for_update(self, *, organization_id: UUID, car_id: UUID) -> CarDTO | None:
        result = await self.session.execute(
            select(Car)
            .where(
                Car.id == car_id,
                Car.organization_id == organization_id,
            )
            .with_for_update(),
        )
        instance = result.scalar_one_or_none()
        return self._to_dto(instance) if instance is not None else None

    async def get_by_license_plate(self, *, organization_id: UUID, license_plate: str) -> CarDTO | None:
        result = await self.session.execute(
            select(Car).where(
                Car.organization_id == organization_id,
                Car.license_plate == license_plate,
            ),
        )
        instance = result.scalar_one_or_none()
        return self._to_dto(instance) if instance is not None else None

    async def list_for_organization(
        self,
        organization_id: UUID,
        *,
        statuses: list[CarStatus] | None = None,
        city: str | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[CarDTO]:
        statement = (
            select(Car)
            .where(Car.organization_id == organization_id)
            .order_by(Car.brand, Car.model, Car.license_plate)
            .offset(offset)
        )

        if statuses:
            statement = statement.where(Car.status.in_(statuses))
        if city is not None:
            statement = statement.where(Car.city == city)
        if limit is not None:
            statement = statement.limit(limit)

        result = await self.session.execute(statement)
        return self._to_dtos(result.scalars().all())

    async def list_by_ids_for_organization(self, *, organization_id: UUID, car_ids: list[UUID]) -> list[CarDTO]:
        if not car_ids:
            return []

        result = await self.session.execute(
            select(Car)
            .where(
                Car.organization_id == organization_id,
                Car.id.in_(car_ids),
            )
            .order_by(Car.brand, Car.model, Car.license_plate),
        )
        return self._to_dtos(result.scalars().all())

    async def search_for_organization(
        self,
        organization_id: UUID,
        query: str,
        *,
        limit: int = 10,
    ) -> list[CarDTO]:
        pattern = f"%{query}%"
        result = await self.session.execute(
            select(Car)
            .where(
                Car.organization_id == organization_id,
                or_(
                    func.concat(Car.brand, " ", Car.model).ilike(pattern),
                    Car.license_plate.ilike(pattern),
                ),
            )
            .order_by(Car.brand, Car.model)
            .limit(limit),
        )
        return self._to_dtos(result.scalars().all())

    async def set_status(self, car_id: UUID, status: CarStatus) -> CarDTO | None:
        instance = await self.session.get(Car, car_id)
        if instance is None:
            return None
        instance.status = status
        await self.session.flush()
        return self._to_dto(instance)

    async def update_mileage(self, car_id: UUID, mileage: int) -> CarDTO | None:
        instance = await self.session.get(Car, car_id)
        if instance is None:
            return None
        instance.mileage = mileage
        await self.session.flush()
        return self._to_dto(instance)


class CarPhotoRepository(BaseRepository[CarPhoto, CarPhotoDTO]):
    model = CarPhoto
    dto = CarPhotoDTO

    async def list_for_car(self, car_id: UUID) -> list[CarPhotoDTO]:
        result = await self.session.execute(
            select(CarPhoto).where(CarPhoto.car_id == car_id).order_by(CarPhoto.position, CarPhoto.created_at),
        )
        return self._to_dtos(result.scalars().all())

    async def delete_for_car(self, car_id: UUID) -> int:
        result = await self.session.execute(delete(CarPhoto).where(CarPhoto.car_id == car_id))
        return result.rowcount


class CarPricingTierRepository(BaseRepository[CarPricingTier, CarPricingTierDTO]):
    model = CarPricingTier
    dto = CarPricingTierDTO

    async def list_for_car(self, car_id: UUID) -> list[CarPricingTierDTO]:
        result = await self.session.execute(
            select(CarPricingTier).where(CarPricingTier.car_id == car_id).order_by(CarPricingTier.min_days),
        )
        return self._to_dtos(result.scalars().all())

    async def get_by_min_days(self, *, car_id: UUID, min_days: int) -> CarPricingTierDTO | None:
        result = await self.session.execute(
            select(CarPricingTier).where(
                CarPricingTier.car_id == car_id,
                CarPricingTier.min_days == min_days,
            ),
        )
        instance = result.scalar_one_or_none()
        return self._to_dto(instance) if instance is not None else None

    async def get_applicable_for_duration(self, *, car_id: UUID, rental_days: int) -> CarPricingTierDTO | None:
        result = await self.session.execute(
            select(CarPricingTier)
            .where(
                CarPricingTier.car_id == car_id,
                CarPricingTier.min_days <= rental_days,
            )
            .order_by(desc(CarPricingTier.min_days))
            .limit(1),
        )
        instance = result.scalar_one_or_none()
        return self._to_dto(instance) if instance is not None else None

    async def set_daily_rate(self, pricing_tier_id: UUID, daily_rate: Decimal) -> CarPricingTierDTO | None:
        instance = await self.session.get(CarPricingTier, pricing_tier_id)
        if instance is None:
            return None
        instance.daily_rate = daily_rate
        await self.session.flush()
        return self._to_dto(instance)

    async def delete_for_car(self, car_id: UUID) -> int:
        result = await self.session.execute(delete(CarPricingTier).where(CarPricingTier.car_id == car_id))
        return result.rowcount


class CarRepairPeriodRepository(BaseRepository[CarRepairPeriod, CarRepairPeriodDTO]):
    model = CarRepairPeriod
    dto = CarRepairPeriodDTO

    async def list_for_car(self, car_id: UUID) -> list[CarRepairPeriodDTO]:
        result = await self.session.execute(
            select(CarRepairPeriod)
            .where(CarRepairPeriod.car_id == car_id)
            .order_by(CarRepairPeriod.date_from),
        )
        return self._to_dtos(result.scalars().all())

    async def list_for_organization_in_range(
        self,
        organization_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[CarRepairPeriodDTO]:
        result = await self.session.execute(
            select(CarRepairPeriod)
            .join(Car, Car.id == CarRepairPeriod.car_id)
            .where(
                Car.organization_id == organization_id,
                CarRepairPeriod.date_from <= date_to,
                CarRepairPeriod.date_to >= date_from,
            )
            .order_by(CarRepairPeriod.date_from),
        )
        return self._to_dtos(result.scalars().all())
