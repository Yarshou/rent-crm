from datetime import date
from decimal import Decimal
from uuid import UUID

from db.models import CarStatus, Currency, DriveType, FuelType, Transmission
from pydantic import BaseModel, Field
from schemas.base.common import BaseEntityResponse

__all__ = [
    "CarCreateRequest",
    "CarPhotoRequest",
    "CarPhotoResponse",
    "CarPricingTierRequest",
    "CarPricingTierResponse",
    "CarRepairPeriodCreateRequest",
    "CarRepairPeriodResponse",
    "CarResponse",
    "CarStatusUpdateRequest",
    "CarUpdateRequest",
]


class CarPhotoRequest(BaseModel):
    file_path: str = Field(min_length=1, max_length=512)
    position: int = Field(default=0, ge=0)


class CarPricingTierRequest(BaseModel):
    min_days: int = Field(gt=0)
    daily_rate: Decimal = Field(ge=0)
    currency: Currency


class CarCreateRequest(BaseModel):
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(gt=0)
    license_plate: str = Field(min_length=1, max_length=20)
    vin: str | None = Field(default=None, max_length=32)
    drive_type: DriveType
    fuel_type: FuelType
    transmission: Transmission
    mileage: int = Field(ge=0)
    city: str = Field(min_length=1, max_length=100)
    status: CarStatus = CarStatus.available
    photos: list[CarPhotoRequest] = Field(default_factory=list)
    pricing_tiers: list[CarPricingTierRequest] = Field(default_factory=list)


class CarUpdateRequest(BaseModel):
    brand: str = Field(default=None, min_length=1, max_length=100)
    model: str = Field(default=None, min_length=1, max_length=100)
    year: int = Field(default=None, gt=0)
    license_plate: str = Field(default=None, min_length=1, max_length=20)
    vin: str | None = Field(default=None, max_length=32)
    drive_type: DriveType = None
    fuel_type: FuelType = None
    transmission: Transmission = None
    mileage: int = Field(default=None, ge=0)
    city: str = Field(default=None, min_length=1, max_length=100)


class CarStatusUpdateRequest(BaseModel):
    status: CarStatus


class CarResponse(BaseEntityResponse):
    organization_id: UUID
    brand: str
    model: str
    year: int
    license_plate: str
    vin: str | None
    drive_type: DriveType
    fuel_type: FuelType
    transmission: Transmission
    mileage: int
    city: str
    status: CarStatus


class CarPhotoResponse(BaseEntityResponse):
    car_id: UUID
    file_path: str
    position: int


class CarPricingTierResponse(BaseEntityResponse):
    car_id: UUID
    min_days: int
    daily_rate: Decimal
    currency: Currency


class CarRepairPeriodCreateRequest(BaseModel):
    date_from: date
    date_to: date
    title: str | None = Field(default=None, max_length=200)


class CarRepairPeriodResponse(BaseEntityResponse):
    car_id: UUID
    date_from: date
    date_to: date
    title: str | None = None
