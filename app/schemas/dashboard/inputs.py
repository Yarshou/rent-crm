from datetime import date
from uuid import UUID

from schemas.base import MutableDTO

__all__ = ["DashboardSummaryInput"]


class DashboardSummaryInput(MutableDTO):
    organization_id: UUID
    target_date: date
