import enum

from db.base.models import Base
from sqlalchemy import Boolean, CheckConstraint, Column, Date, Enum, ForeignKey, Integer, Numeric, String, Text, Uuid

__all__ = ["MaintenanceRecord", "MaintenanceSchedule", "ServiceType"]


class ServiceType(str, enum.Enum):
    oil_change = "oil_change"
    tires = "tires"
    brakes = "brakes"
    inspection = "inspection"
    repair = "repair"
    other = "other"


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    car_id = Column(Uuid, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    service_date = Column(Date, nullable=False)
    service_type = Column(Enum(ServiceType, name="service_type"), nullable=False)
    description = Column(Text, nullable=False)
    mileage_at_service = Column(Integer, nullable=False)
    cost = Column(Numeric(12, 2), nullable=False)
    provider = Column(String(255), nullable=True)


class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"
    __table_args__ = (
        CheckConstraint(
            "scheduled_date IS NOT NULL OR scheduled_mileage IS NOT NULL",
            name="ck_maintenance_schedules_date_or_mileage",
        ),
    )

    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    car_id = Column(Uuid, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    service_type = Column(Enum(ServiceType, name="service_type"), nullable=False)
    scheduled_date = Column(Date, nullable=True)
    scheduled_mileage = Column(Integer, nullable=True)
    interval_km = Column(Integer, nullable=True)
    is_completed = Column(Boolean, nullable=False, default=False)
    maintenance_record_id = Column(
        Uuid,
        ForeignKey("maintenance_records.id", ondelete="SET NULL"),
        nullable=True,
    )
