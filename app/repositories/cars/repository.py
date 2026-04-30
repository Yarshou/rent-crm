from decimal import Decimal
from uuid import UUID

from db.models import Car, CarPhoto, CarPricingTier, CarStatus
from repositories import BaseRepository
from sqlalchemy import delete, desc, select

__all__ = ["CarPhotoRepository", "CarPricingTierRepository", "CarRepository"]


class CarRepository(BaseRepository[Car]):
    model = Car

    async def get_for_organization(self, *, organization_id: UUID, car_id: UUID) -> Car | None:
        result = await self.session.execute(
            select(Car).where(
                Car.id == car_id,
                Car.organization_id == organization_id,
            ),
        )
        return result.scalar_one_or_none()

    async def get_for_organization_for_update(self, *, organization_id: UUID, car_id: UUID) -> Car | None:
        result = await self.session.execute(
            select(Car)
            .where(
                Car.id == car_id,
                Car.organization_id == organization_id,
            )
            .with_for_update(),
        )
        return result.scalar_one_or_none()

    async def get_by_license_plate(self, *, organization_id: UUID, license_plate: str) -> Car | None:
        result = await self.session.execute(
            select(Car).where(
                Car.organization_id == organization_id,
                Car.license_plate == license_plate,
            ),
        )
        return result.scalar_one_or_none()

    async def list_for_organization(
        self,
        organization_id: UUID,
        *,
        statuses: list[CarStatus] | None = None,
        city: str | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[Car]:
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
        return list(result.scalars().all())

    async def list_by_ids_for_organization(self, *, organization_id: UUID, car_ids: list[UUID]) -> list[Car]:
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
        return list(result.scalars().all())

    async def set_status(self, car: Car, status: CarStatus) -> Car:
        car.status = status
        return car

    async def update_mileage(self, car: Car, mileage: int) -> Car:
        car.mileage = mileage
        return car


class CarPhotoRepository(BaseRepository[CarPhoto]):
    model = CarPhoto

    async def list_for_car(self, car_id: UUID) -> list[CarPhoto]:
        result = await self.session.execute(
            select(CarPhoto).where(CarPhoto.car_id == car_id).order_by(CarPhoto.position, CarPhoto.created_at),
        )
        return list(result.scalars().all())

    async def delete_for_car(self, car_id: UUID) -> int:
        result = await self.session.execute(delete(CarPhoto).where(CarPhoto.car_id == car_id))
        return result.rowcount


class CarPricingTierRepository(BaseRepository[CarPricingTier]):
    model = CarPricingTier

    async def list_for_car(self, car_id: UUID) -> list[CarPricingTier]:
        result = await self.session.execute(
            select(CarPricingTier).where(CarPricingTier.car_id == car_id).order_by(CarPricingTier.min_days),
        )
        return list(result.scalars().all())

    async def get_by_min_days(self, *, car_id: UUID, min_days: int) -> CarPricingTier | None:
        result = await self.session.execute(
            select(CarPricingTier).where(
                CarPricingTier.car_id == car_id,
                CarPricingTier.min_days == min_days,
            ),
        )
        return result.scalar_one_or_none()

    async def get_applicable_for_duration(self, *, car_id: UUID, rental_days: int) -> CarPricingTier | None:
        result = await self.session.execute(
            select(CarPricingTier)
            .where(
                CarPricingTier.car_id == car_id,
                CarPricingTier.min_days <= rental_days,
            )
            .order_by(desc(CarPricingTier.min_days))
            .limit(1),
        )
        return result.scalar_one_or_none()

    async def set_daily_rate(self, pricing_tier: CarPricingTier, daily_rate: Decimal) -> CarPricingTier:
        pricing_tier.daily_rate = daily_rate
        return pricing_tier

    async def delete_for_car(self, car_id: UUID) -> int:
        result = await self.session.execute(delete(CarPricingTier).where(CarPricingTier.car_id == car_id))
        return result.rowcount
