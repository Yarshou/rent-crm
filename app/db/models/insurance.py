from db.base.models import Base
from db.models.common import Currency
from sqlalchemy import Column, Date, Enum, ForeignKey, Numeric, String, Text, Uuid

__all__ = ["InsurancePayment"]


class InsurancePayment(Base):
    __tablename__ = "insurance_payments"

    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    car_id = Column(Uuid, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_date = Column(Date, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(Enum(Currency, name="currency"), nullable=False)
    provider = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
