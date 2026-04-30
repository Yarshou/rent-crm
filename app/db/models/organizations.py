from db.base.models import Base
from sqlalchemy import Column, String

__all__ = ["Organization"]


class Organization(Base):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
