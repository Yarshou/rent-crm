from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

__all__ = ["AmountResponse", "BaseEntityResponse"]


class BaseEntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AmountResponse(BaseModel):
    total_amount: Decimal
    currency: str
