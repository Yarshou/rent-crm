from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from db.models import CarStatus, DriveType, FuelType, Transmission
from schemas.base import MutableDTO

__all__ = [
    "CarCreateInput",
    "CarDeleteInput",
    "CarGetInput",
    "CarListInput",
    "CarPhotoInput",
    "CarPhotoUploadInput",
    "CarPhotosListInput",
    "CarPhotosReplaceInput",
    "CarPricingTierInput",
    "CarPricingTiersListInput",
    "CarPricingTiersReplaceInput",
    "CarStatusUpdateInput",
    "CarUpdateInput",
]


class CarPhotoInput(MutableDTO):
    file_path: str
    position: int = 0


class CarPricingTierInput(MutableDTO):
    min_days: int
    daily_rate: Decimal


class CarGetInput(MutableDTO):
    organization_id: UUID
    car_id: UUID


class CarListInput(MutableDTO):
    organization_id: UUID
    statuses: list[CarStatus] | None = None
    city: str | None = None
    offset: int = 0
    limit: int | None = None


class CarCreateInput(MutableDTO):
    organization_id: UUID
    brand: str
    model: str
    year: int
    license_plate: str
    vin: str | None = None
    drive_type: DriveType
    fuel_type: FuelType
    transmission: Transmission
    mileage: int
    city: str
    status: CarStatus = CarStatus.available
    photos: Sequence[CarPhotoInput] = ()
    pricing_tiers: Sequence[CarPricingTierInput] = ()


class CarUpdateInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    license_plate: str | None = None
    vin: str | None = None
    drive_type: DriveType | None = None
    fuel_type: FuelType | None = None
    transmission: Transmission | None = None
    mileage: int | None = None
    city: str | None = None


class CarStatusUpdateInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    status: CarStatus


class CarDeleteInput(MutableDTO):
    organization_id: UUID
    car_id: UUID


class CarPhotosListInput(MutableDTO):
    organization_id: UUID
    car_id: UUID


class CarPhotosReplaceInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    photos: Sequence[CarPhotoInput]


class CarPhotoUploadInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    filename: str
    content: bytes
    position: int = 0
    content_type: str | None = None


class CarPricingTiersListInput(MutableDTO):
    organization_id: UUID
    car_id: UUID


class CarPricingTiersReplaceInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    pricing_tiers: Sequence[CarPricingTierInput]
