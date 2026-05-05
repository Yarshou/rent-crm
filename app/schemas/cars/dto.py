from datetime import datetime
from decimal import Decimal
from uuid import UUID

from db.models import CarStatus, DriveType, FuelType, Transmission
from schemas.base import ImmutableDTO

__all__ = ["CarDTO", "CarPhotoDTO", "CarPricingTierDTO"]


class CarDTO(ImmutableDTO):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
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
    status: CarStatus


class CarPhotoDTO(ImmutableDTO):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    car_id: UUID
    file_path: str
    position: int


class CarPricingTierDTO(ImmutableDTO):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    car_id: UUID
    min_days: int
    daily_rate: Decimal
