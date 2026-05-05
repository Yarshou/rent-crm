from datetime import date
from uuid import UUID

from schemas.base import MutableDTO

__all__ = ["CalendarRangeInput"]


class CalendarRangeInput(MutableDTO):
    organization_id: UUID
    date_from: date
    date_to: date
