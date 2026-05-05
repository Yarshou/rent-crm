from datetime import date
from uuid import UUID

from schemas.base import MutableDTO

__all__ = ["CarDetailsInput"]


class CarDetailsInput(MutableDTO):
    organization_id: UUID
    car_id: UUID
    today: date
