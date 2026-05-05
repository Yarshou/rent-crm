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
    income: Decimal
    maintenance_expenses: Decimal
    insurance_expenses: Decimal
    expenses: Decimal
    net: Decimal


class CarRevenueRankResponse(BaseModel):
    car_id: UUID
    label: str
    license_plate: str
    booking_count: int
    booked_days: int
    income: Decimal


class ExpenseBreakdownResponse(BaseModel):
    category: str
    amount: Decimal
    share: Decimal


class ReportsSummaryResponse(BaseModel):
    year: int
    monthly: list[MonthlyReportResponse]
    car_ranking: list[CarRevenueRankResponse]
    expense_breakdown: list[ExpenseBreakdownResponse]
