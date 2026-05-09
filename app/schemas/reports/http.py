from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

__all__ = [
    "CarRevenueRankResponse",
    "ExpenseBreakdownResponse",
    "MonthlyReportResponse",
    "ReportsSummaryResponse",
]


class MonthlyReportResponse(BaseModel):
    month: int
    income_usd: Decimal
    income_gel: Decimal
    maintenance_expenses_usd: Decimal
    maintenance_expenses_gel: Decimal
    insurance_expenses_usd: Decimal
    insurance_expenses_gel: Decimal
    expenses_usd: Decimal
    expenses_gel: Decimal
    net_usd: Decimal
    net_gel: Decimal


class CarRevenueRankResponse(BaseModel):
    car_id: UUID
    label: str
    license_plate: str
    booking_count: int
    booked_days: int
    income_usd: Decimal
    income_gel: Decimal


class ExpenseBreakdownResponse(BaseModel):
    category: str
    amount_usd: Decimal
    amount_gel: Decimal
    share_usd: Decimal
    share_gel: Decimal


class ReportsSummaryResponse(BaseModel):
    year: int
    monthly: list[MonthlyReportResponse]
    car_ranking: list[CarRevenueRankResponse]
    expense_breakdown: list[ExpenseBreakdownResponse]
