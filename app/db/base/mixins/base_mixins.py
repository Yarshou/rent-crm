import uuid

from sqlalchemy import TIMESTAMP, Column, Uuid
from sqlalchemy.sql.functions import now

__all__ = ["BaseMixin"]


class BaseMixin:
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at = Column(TIMESTAMP(timezone=True), default=now, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=now, nullable=True)
