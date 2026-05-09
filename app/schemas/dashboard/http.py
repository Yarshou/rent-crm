from datetime import date
from decimal import Decimal

from pydantic import BaseModel

__all__ = ["BookingSummaryResponse", "DashboardSummaryResponse", "FleetSummaryResponse", "MoneySummaryResponse"]


class FleetSummaryResponse(BaseModel):
    total: int
    available: int
    rented: int
    in_repair: int


class BookingSummaryResponse(BaseModel):
    active: int
    planned: int
    pickups_today: int
    returns_today: int
    overdue_returns: int


class MoneySummaryResponse(BaseModel):
    income_mtd_usd: Decimal
    income_mtd_gel: Decimal
    expenses_mtd_usd: Decimal
    expenses_mtd_gel: Decimal
    net_mtd_usd: Decimal
    net_mtd_gel: Decimal


class DashboardSummaryResponse(BaseModel):
    date: date
    fleet: FleetSummaryResponse
    bookings: BookingSummaryResponse
    money: MoneySummaryResponse
    occupancy: Decimal
