import enum

from db.base.models import Base
from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, Numeric, String, Text, Uuid

__all__ = ["Booking", "BookingStatus"]


class BookingStatus(str, enum.Enum):
    planned = "planned"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class Booking(Base):
    __tablename__ = "bookings"

    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    car_id = Column(Uuid, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    renter_name = Column(String(255), nullable=False)
    renter_phone = Column(String(32), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    pickup_mileage = Column(Integer, nullable=True)
    return_mileage = Column(Integer, nullable=True)
    status = Column(Enum(BookingStatus, name="booking_status"), nullable=False, default=BookingStatus.planned)
    notes = Column(Text, nullable=True)
