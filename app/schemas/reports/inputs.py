from uuid import UUID

from schemas.base import MutableDTO

__all__ = ["ReportsSummaryInput"]


class ReportsSummaryInput(MutableDTO):
    organization_id: UUID
    year: int
