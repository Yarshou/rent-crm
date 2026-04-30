import enum

from db.base.models import Base
from sqlalchemy import Column, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid

__all__ = [
    "Car",
    "CarPhoto",
    "CarPricingTier",
    "DriveType",
    "FuelType",
    "Transmission",
    "CarStatus",
]


class DriveType(str, enum.Enum):
    fwd = "FWD"
    rwd = "RWD"
    awd = "AWD"
    four_wd = "4WD"


class FuelType(str, enum.Enum):
    petrol = "petrol"
    diesel = "diesel"
    hybrid = "hybrid"
    electric = "electric"
    gas = "gas"


class Transmission(str, enum.Enum):
    manual = "manual"
    automatic = "automatic"
    robot = "robot"
    variator = "variator"


class CarStatus(str, enum.Enum):
    available = "available"
    rented = "rented"
    in_repair = "in_repair"


class Car(Base):
    __tablename__ = "cars"

    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    license_plate = Column(String(20), nullable=False, index=True)
    vin = Column(String(32), nullable=True)
    drive_type = Column(Enum(DriveType, name="drive_type"), nullable=False)
    fuel_type = Column(Enum(FuelType, name="fuel_type"), nullable=False)
    transmission = Column(Enum(Transmission, name="transmission"), nullable=False)
    mileage = Column(Integer, nullable=False, default=0)
    city = Column(String(100), nullable=False)
    status = Column(Enum(CarStatus, name="car_status"), nullable=False, default=CarStatus.available)


class CarPhoto(Base):
    __tablename__ = "car_photos"

    car_id = Column(Uuid, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    position = Column(Integer, nullable=False, default=0)


class CarPricingTier(Base):
    __tablename__ = "car_pricing_tiers"
    __table_args__ = (UniqueConstraint("car_id", "min_days", name="uq_car_pricing_tiers_car_min_days"),)

    car_id = Column(Uuid, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    min_days = Column(Integer, nullable=False)
    daily_rate = Column(Numeric(12, 2), nullable=False)
