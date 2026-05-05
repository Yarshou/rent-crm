from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from re import sub
from uuid import UUID, uuid4

from config.settings import settings
from db.models import CarStatus
from repositories import UnitOfWork
from schemas.cars import (
    CarCreateInput,
    CarDeleteInput,
    CarDTO,
    CarGetInput,
    CarListInput,
    CarPhotoDTO,
    CarPhotoInput,
    CarPhotosListInput,
    CarPhotosReplaceInput,
    CarPhotoUploadInput,
    CarPricingTierDTO,
    CarPricingTierInput,
    CarPricingTiersListInput,
    CarPricingTiersReplaceInput,
    CarStatusUpdateInput,
    CarUpdateInput,
)

from ..common import ServiceConflictError, ServiceNotFoundError, ServiceValidationError, UnitOfWorkFactory

__all__ = ["CarService"]

_UPDATABLE_FIELDS = {
    "brand",
    "model",
    "year",
    "license_plate",
    "vin",
    "drive_type",
    "fuel_type",
    "transmission",
    "mileage",
    "city",
}


class CarService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get(self, input: CarGetInput) -> CarDTO:
        async with self._uow_factory() as uow:
            return await self._get_car(uow, organization_id=input.organization_id, car_id=input.car_id)

    async def list(self, input: CarListInput) -> list[CarDTO]:
        async with self._uow_factory() as uow:
            return await uow.cars.list_for_organization(
                input.organization_id,
                statuses=input.statuses,
                city=input.city,
                offset=input.offset,
                limit=input.limit,
            )

    async def create(self, input: CarCreateInput) -> CarDTO:
        self._validate_year(input.year)
        self._validate_mileage(input.mileage)
        self._validate_pricing_tiers(input.pricing_tiers)
        self._validate_photos(input.photos)
        if input.status == CarStatus.rented:
            raise ServiceValidationError("Car cannot be created as rented without an active booking.")

        async with self._uow_factory() as uow:
            await self._ensure_organization_exists(uow, input.organization_id)
            await self._ensure_license_plate_available(
                uow,
                organization_id=input.organization_id,
                license_plate=input.license_plate,
            )

            car = await uow.cars.create(
                organization_id=input.organization_id,
                brand=input.brand,
                model=input.model,
                year=input.year,
                license_plate=input.license_plate,
                vin=input.vin,
                drive_type=input.drive_type,
                fuel_type=input.fuel_type,
                transmission=input.transmission,
                mileage=input.mileage,
                city=input.city,
                status=input.status,
            )

            for photo in input.photos:
                await uow.car_photos.create(car_id=car.id, file_path=photo.file_path, position=photo.position)
            for tier in input.pricing_tiers:
                await uow.car_pricing_tiers.create(
                    car_id=car.id,
                    min_days=tier.min_days,
                    daily_rate=tier.daily_rate,
                )

            await uow.commit()
            return car

    async def update(self, input: CarUpdateInput) -> CarDTO:
        values = input.model_dump(exclude={"organization_id", "car_id"}, exclude_unset=True, exclude_none=True)
        unknown_fields = set(values) - _UPDATABLE_FIELDS
        if unknown_fields:
            raise ServiceValidationError(f"Unsupported car fields: {', '.join(sorted(unknown_fields))}.")

        async with self._uow_factory() as uow:
            car = await self._get_car_for_update(uow, organization_id=input.organization_id, car_id=input.car_id)

            if "year" in values:
                self._validate_year(values["year"])
            if "mileage" in values:
                self._validate_mileage(values["mileage"])
                if values["mileage"] < car.mileage:
                    raise ServiceValidationError("Car mileage cannot decrease.")
            if "license_plate" in values and values["license_plate"] != car.license_plate:
                await self._ensure_license_plate_available(
                    uow,
                    organization_id=input.organization_id,
                    license_plate=values["license_plate"],
                )

            if not values:
                return car

            updated = await uow.cars.update(input.car_id, **values)
            if updated is None:
                raise ServiceNotFoundError("Car not found.")
            await uow.commit()
            return updated

    async def set_status(self, input: CarStatusUpdateInput) -> CarDTO:
        async with self._uow_factory() as uow:
            car = await self._get_car_for_update(uow, organization_id=input.organization_id, car_id=input.car_id)
            active_bookings_count = await uow.bookings.count_active_for_car(
                organization_id=input.organization_id,
                car_id=input.car_id,
            )

            if input.status == CarStatus.available and active_bookings_count > 0:
                raise ServiceConflictError("Car has active bookings and cannot be marked as available.")
            if input.status == CarStatus.in_repair and active_bookings_count > 0:
                raise ServiceConflictError("Car has active bookings and cannot be marked as in repair.")
            if input.status == CarStatus.rented and active_bookings_count == 0:
                raise ServiceConflictError("Car cannot be marked as rented without active bookings.")

            updated = await uow.cars.set_status(car.id, input.status)
            if updated is None:
                raise ServiceNotFoundError("Car not found.")
            await uow.commit()
            return updated

    async def list_photos(self, input: CarPhotosListInput) -> list[CarPhotoDTO]:
        async with self._uow_factory() as uow:
            await self._get_car(uow, organization_id=input.organization_id, car_id=input.car_id)
            return await uow.car_photos.list_for_car(input.car_id)

    async def replace_photos(self, input: CarPhotosReplaceInput) -> list[CarPhotoDTO]:
        self._validate_photos(input.photos)

        async with self._uow_factory() as uow:
            await self._get_car_for_update(uow, organization_id=input.organization_id, car_id=input.car_id)
            await uow.car_photos.delete_for_car(input.car_id)

            created_photos = [
                await uow.car_photos.create(car_id=input.car_id, file_path=photo.file_path, position=photo.position)
                for photo in input.photos
            ]
            await uow.commit()
            return created_photos

    async def upload_photo(self, input: CarPhotoUploadInput) -> CarPhotoDTO:
        self._validate_photo_upload(filename=input.filename, content=input.content, content_type=input.content_type)
        safe_filename = self._build_photo_filename(input.filename)
        relative_path = Path("car-photos") / str(input.organization_id) / str(input.car_id) / safe_filename
        target_path = settings.MEDIA_ROOT / relative_path

        async with self._uow_factory() as uow:
            await self._get_car(uow, organization_id=input.organization_id, car_id=input.car_id)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(input.content)
            photo = await uow.car_photos.create(
                car_id=input.car_id,
                file_path=f"{settings.MEDIA_URL.rstrip('/')}/{relative_path.as_posix()}",
                position=input.position,
            )
            await uow.commit()
            return photo

    async def list_pricing_tiers(self, input: CarPricingTiersListInput) -> list[CarPricingTierDTO]:
        async with self._uow_factory() as uow:
            await self._get_car(uow, organization_id=input.organization_id, car_id=input.car_id)
            return await uow.car_pricing_tiers.list_for_car(input.car_id)

    async def replace_pricing_tiers(self, input: CarPricingTiersReplaceInput) -> list[CarPricingTierDTO]:
        self._validate_pricing_tiers(input.pricing_tiers)

        async with self._uow_factory() as uow:
            await self._get_car_for_update(uow, organization_id=input.organization_id, car_id=input.car_id)
            await uow.car_pricing_tiers.delete_for_car(input.car_id)

            created_tiers = [
                await uow.car_pricing_tiers.create(
                    car_id=input.car_id,
                    min_days=tier.min_days,
                    daily_rate=tier.daily_rate,
                )
                for tier in input.pricing_tiers
            ]
            await uow.commit()
            return created_tiers

    async def delete(self, input: CarDeleteInput) -> None:
        async with self._uow_factory() as uow:
            await self._get_car_for_update(uow, organization_id=input.organization_id, car_id=input.car_id)
            active_bookings_count = await uow.bookings.count_active_for_car(
                organization_id=input.organization_id,
                car_id=input.car_id,
            )
            if active_bookings_count > 0:
                raise ServiceConflictError("Car with active bookings cannot be deleted.")

            deleted = await uow.cars.delete_by_id(input.car_id)
            if not deleted:
                raise ServiceNotFoundError("Car not found.")

            await uow.commit()

    async def _get_car(self, uow: UnitOfWork, *, organization_id: UUID, car_id: UUID) -> CarDTO:
        car = await uow.cars.get_for_organization(organization_id=organization_id, car_id=car_id)
        if car is None:
            raise ServiceNotFoundError("Car not found.")
        return car

    async def _get_car_for_update(self, uow: UnitOfWork, *, organization_id: UUID, car_id: UUID) -> CarDTO:
        car = await uow.cars.get_for_organization_for_update(organization_id=organization_id, car_id=car_id)
        if car is None:
            raise ServiceNotFoundError("Car not found.")
        return car

    async def _ensure_organization_exists(self, uow: UnitOfWork, organization_id: UUID) -> None:
        organization = await uow.organizations.get(organization_id)
        if organization is None:
            raise ServiceNotFoundError("Organization not found.")

    async def _ensure_license_plate_available(
        self,
        uow: UnitOfWork,
        *,
        organization_id: UUID,
        license_plate: str,
    ) -> None:
        existing = await uow.cars.get_by_license_plate(organization_id=organization_id, license_plate=license_plate)
        if existing is not None:
            raise ServiceConflictError("Car with this license plate already exists in the organization.")

    def _validate_pricing_tiers(self, pricing_tiers: Sequence[CarPricingTierInput]) -> None:
        min_days_values = [tier.min_days for tier in pricing_tiers]
        if len(min_days_values) != len(set(min_days_values)):
            raise ServiceValidationError("Pricing tiers must have unique min_days values.")

        for tier in pricing_tiers:
            if tier.min_days <= 0:
                raise ServiceValidationError("Pricing tier min_days must be positive.")
            if tier.daily_rate < 0:
                raise ServiceValidationError("Pricing tier daily_rate cannot be negative.")

    def _validate_photos(self, photos: Sequence[CarPhotoInput]) -> None:
        for photo in photos:
            if photo.position < 0:
                raise ServiceValidationError("Photo position cannot be negative.")

    def _validate_photo_upload(self, *, filename: str, content: bytes, content_type: str | None) -> None:
        if not filename.strip():
            raise ServiceValidationError("Photo filename is required.")
        if not content:
            raise ServiceValidationError("Photo file is empty.")
        if len(content) > settings.MEDIA_MAX_UPLOAD_BYTES:
            raise ServiceValidationError("Photo file is too large.")
        if content_type is not None and not content_type.startswith("image/"):
            raise ServiceValidationError("Only image uploads are supported.")

    def _build_photo_filename(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"

        stem = sub(r"[^a-zA-Z0-9_-]+", "-", Path(filename).stem).strip("-").lower() or "photo"
        return f"{stem}-{uuid4().hex}{suffix}"

    def _validate_year(self, year: int) -> None:
        if year <= 0:
            raise ServiceValidationError("Car year must be positive.")

    def _validate_mileage(self, mileage: int) -> None:
        if mileage < 0:
            raise ServiceValidationError("Car mileage cannot be negative.")
