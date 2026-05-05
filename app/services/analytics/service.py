from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from db.models import BookingStatus, CarStatus
from schemas import (
    BookingDTO,
    BookingSummaryResponse,
    CalendarRangeInput,
    CalendarResponse,
    CarDetailsInput,
    CarDetailsResponse,
    CarDTO,
    CarMaintenanceDetailsResponse,
    CarRevenueRankResponse,
    DashboardSummaryInput,
    DashboardSummaryResponse,
    ExpenseBreakdownResponse,
    FleetSummaryResponse,
    InsurancePaymentDTO,
    MaintenanceRecordDTO,
    MoneySummaryResponse,
    MonthlyReportResponse,
    ReportsSummaryInput,
    ReportsSummaryResponse,
)

from ..common import ServiceNotFoundError, ServiceValidationError, UnitOfWorkFactory

__all__ = ["AnalyticsService"]

_MONEY_ZERO = Decimal("0.00")
_RATIO_ZERO = Decimal("0.00")
_ACTIVE_PLANNED_STATUSES = [BookingStatus.active, BookingStatus.planned]
_VISIBLE_BOOKING_STATUSES = [BookingStatus.active, BookingStatus.planned, BookingStatus.completed]


class AnalyticsService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_dashboard_summary(self, input: DashboardSummaryInput) -> DashboardSummaryResponse:
        target_date = input.target_date
        month_start = target_date.replace(day=1)

        async with self._uow_factory() as uow:
            cars = await uow.cars.list_for_organization(input.organization_id)
            active_bookings = await uow.bookings.list_for_organization(
                input.organization_id,
                statuses=[BookingStatus.active],
            )
            planned_bookings = await uow.bookings.list_for_organization(
                input.organization_id,
                statuses=[BookingStatus.planned],
            )
            visible_bookings_mtd = await uow.bookings.list_for_organization(
                input.organization_id,
                statuses=_VISIBLE_BOOKING_STATUSES,
                date_from=month_start,
                date_to=target_date,
            )
            maintenance_mtd = await uow.maintenance_records.list_for_organization(
                input.organization_id,
                date_from=month_start,
                date_to=target_date,
            )
            insurance_mtd = await uow.insurance_payments.list_for_organization(
                input.organization_id,
                payment_date_from=month_start,
                payment_date_to=target_date,
            )

        fleet = self._build_fleet_summary(cars)
        income_mtd = self._sum_booking_income(
            booking
            for booking in visible_bookings_mtd
            if month_start <= booking.start_date <= target_date and booking.status != BookingStatus.cancelled
        )
        expenses_mtd = self._sum_maintenance_costs(maintenance_mtd) + self._sum_insurance_costs(insurance_mtd)
        bookings_on_date = [*active_bookings, *planned_bookings]
        occupied_car_ids = {
            booking.car_id
            for booking in bookings_on_date
            if booking.start_date <= target_date <= booking.end_date and booking.status in _ACTIVE_PLANNED_STATUSES
        }

        return DashboardSummaryResponse(
            date=target_date,
            fleet=fleet,
            bookings=BookingSummaryResponse(
                active=len(active_bookings),
                planned=len(planned_bookings),
                pickups_today=sum(
                    1
                    for booking in bookings_on_date
                    if booking.start_date == target_date and booking.status in _ACTIVE_PLANNED_STATUSES
                ),
                returns_today=sum(
                    1
                    for booking in bookings_on_date
                    if booking.end_date == target_date and booking.status in _ACTIVE_PLANNED_STATUSES
                ),
                overdue_returns=sum(1 for booking in active_bookings if booking.end_date < target_date),
            ),
            money=MoneySummaryResponse(
                income_mtd=income_mtd,
                expenses_mtd=expenses_mtd,
                net_mtd=income_mtd - expenses_mtd,
            ),
            occupancy=self._ratio(len(occupied_car_ids), fleet.total),
        )

    async def get_calendar(self, input: CalendarRangeInput) -> CalendarResponse:
        self._validate_date_range(date_from=input.date_from, date_to=input.date_to)

        async with self._uow_factory() as uow:
            cars = await uow.cars.list_for_organization(input.organization_id)
            bookings = await uow.bookings.list_for_organization(
                input.organization_id,
                statuses=_VISIBLE_BOOKING_STATUSES,
                date_from=input.date_from,
                date_to=input.date_to,
            )

        return CalendarResponse(
            date_from=input.date_from,
            date_to=input.date_to,
            cars=cars,
            bookings=bookings,
            repair_periods=[],
        )

    async def get_car_details(self, input: CarDetailsInput) -> CarDetailsResponse:
        async with self._uow_factory() as uow:
            car = await uow.cars.get_for_organization(organization_id=input.organization_id, car_id=input.car_id)
            if car is None:
                raise ServiceNotFoundError("Car not found.")

            photos = await uow.car_photos.list_for_car(car.id)
            pricing_tiers = await uow.car_pricing_tiers.list_for_car(car.id)
            active_bookings = await uow.bookings.list_active_for_car(
                organization_id=input.organization_id,
                car_id=car.id,
            )
            upcoming_bookings = [
                booking
                for booking in await uow.bookings.list_for_car(
                    organization_id=input.organization_id,
                    car_id=car.id,
                    statuses=[BookingStatus.planned],
                    date_from=input.today,
                )
                if booking.start_date >= input.today
            ]
            maintenance_records = await uow.maintenance_records.list_for_car(
                organization_id=input.organization_id,
                car_id=car.id,
            )
            maintenance_schedules = await uow.maintenance_schedules.list_open_for_car(
                organization_id=input.organization_id,
                car_id=car.id,
            )
            insurance = await uow.insurance_payments.list_for_car(
                organization_id=input.organization_id,
                car_id=car.id,
                coverage_from=input.today,
            )

        return CarDetailsResponse(
            car=car,
            photos=photos,
            pricing_tiers=pricing_tiers,
            active_booking=active_bookings[0] if active_bookings else None,
            upcoming_bookings=upcoming_bookings,
            maintenance=CarMaintenanceDetailsResponse(
                records=maintenance_records,
                schedules=maintenance_schedules,
            ),
            insurance=insurance,
        )

    async def get_reports_summary(self, input: ReportsSummaryInput) -> ReportsSummaryResponse:
        if input.year < 2000 or input.year > 2100:
            raise ServiceValidationError("Year must be between 2000 and 2100.")

        date_from = date(input.year, 1, 1)
        date_to = date(input.year, 12, 31)

        async with self._uow_factory() as uow:
            cars = await uow.cars.list_for_organization(input.organization_id)
            bookings = await uow.bookings.list_for_organization(
                input.organization_id,
                statuses=_VISIBLE_BOOKING_STATUSES,
                date_from=date_from,
                date_to=date_to,
            )
            maintenance_records = await uow.maintenance_records.list_for_organization(
                input.organization_id,
                date_from=date_from,
                date_to=date_to,
            )
            insurance_payments = await uow.insurance_payments.list_for_organization(
                input.organization_id,
                payment_date_from=date_from,
                payment_date_to=date_to,
            )

        return ReportsSummaryResponse(
            year=input.year,
            monthly=self._build_monthly_reports(
                bookings=bookings,
                maintenance_records=maintenance_records,
                insurance_payments=insurance_payments,
                year=input.year,
            ),
            car_ranking=self._build_car_ranking(cars=cars, bookings=bookings),
            expense_breakdown=self._build_expense_breakdown(
                maintenance_records=maintenance_records,
                insurance_payments=insurance_payments,
            ),
        )

    def _build_fleet_summary(self, cars: list[CarDTO]) -> FleetSummaryResponse:
        return FleetSummaryResponse(
            total=len(cars),
            available=sum(1 for car in cars if car.status == CarStatus.available),
            rented=sum(1 for car in cars if car.status == CarStatus.rented),
            in_repair=sum(1 for car in cars if car.status == CarStatus.in_repair),
        )

    def _build_monthly_reports(
        self,
        *,
        bookings: list[BookingDTO],
        maintenance_records: list[MaintenanceRecordDTO],
        insurance_payments: list[InsurancePaymentDTO],
        year: int,
    ) -> list[MonthlyReportResponse]:
        monthly_income: dict[int, Decimal] = defaultdict(lambda: _MONEY_ZERO)
        monthly_maintenance: dict[int, Decimal] = defaultdict(lambda: _MONEY_ZERO)
        monthly_insurance: dict[int, Decimal] = defaultdict(lambda: _MONEY_ZERO)

        for booking in bookings:
            if booking.status != BookingStatus.cancelled and booking.start_date.year == year:
                monthly_income[booking.start_date.month] += Decimal(booking.total_amount)
        for record in maintenance_records:
            monthly_maintenance[record.service_date.month] += Decimal(record.cost)
        for payment in insurance_payments:
            monthly_insurance[payment.payment_date.month] += Decimal(payment.amount)

        reports = []
        for month in range(1, 13):
            income = monthly_income[month]
            maintenance = monthly_maintenance[month]
            insurance = monthly_insurance[month]
            expenses = maintenance + insurance
            reports.append(
                MonthlyReportResponse(
                    month=month,
                    income=income,
                    maintenance_expenses=maintenance,
                    insurance_expenses=insurance,
                    expenses=expenses,
                    net=income - expenses,
                ),
            )
        return reports

    def _build_car_ranking(self, *, cars: list[CarDTO], bookings: list[BookingDTO]) -> list[CarRevenueRankResponse]:
        cars_by_id = {car.id: car for car in cars}
        stats: dict[UUID, dict[str, Decimal | int]] = defaultdict(
            lambda: {"income": _MONEY_ZERO, "booking_count": 0, "booked_days": 0},
        )
        for booking in bookings:
            if booking.status == BookingStatus.cancelled or booking.car_id not in cars_by_id:
                continue
            stats[booking.car_id]["income"] += Decimal(booking.total_amount)
            stats[booking.car_id]["booking_count"] += 1
            stats[booking.car_id]["booked_days"] += (booking.end_date - booking.start_date).days + 1

        ranking = []
        for car_id, stat in stats.items():
            car = cars_by_id[car_id]
            ranking.append(
                CarRevenueRankResponse(
                    car_id=car.id,
                    label=f"{car.brand} {car.model}",
                    license_plate=car.license_plate,
                    booking_count=int(stat["booking_count"]),
                    booked_days=int(stat["booked_days"]),
                    income=Decimal(stat["income"]),
                ),
            )

        return sorted(ranking, key=lambda item: item.income, reverse=True)

    def _build_expense_breakdown(
        self,
        *,
        maintenance_records: list[MaintenanceRecordDTO],
        insurance_payments: list[InsurancePaymentDTO],
    ) -> list[ExpenseBreakdownResponse]:
        maintenance = self._sum_maintenance_costs(maintenance_records)
        insurance = self._sum_insurance_costs(insurance_payments)
        total = maintenance + insurance
        return [
            ExpenseBreakdownResponse(
                category="maintenance",
                amount=maintenance,
                share=self._ratio_decimal(maintenance, total),
            ),
            ExpenseBreakdownResponse(
                category="insurance",
                amount=insurance,
                share=self._ratio_decimal(insurance, total),
            ),
        ]

    def _sum_booking_income(self, bookings: Iterable[BookingDTO]) -> Decimal:
        return sum((Decimal(booking.total_amount) for booking in bookings), _MONEY_ZERO)

    def _sum_maintenance_costs(self, records: list[MaintenanceRecordDTO]) -> Decimal:
        return sum((Decimal(record.cost) for record in records), _MONEY_ZERO)

    def _sum_insurance_costs(self, payments: list[InsurancePaymentDTO]) -> Decimal:
        return sum((Decimal(payment.amount) for payment in payments), _MONEY_ZERO)

    def _ratio(self, numerator: int, denominator: int) -> Decimal:
        if denominator == 0:
            return _RATIO_ZERO
        return self._ratio_decimal(Decimal(numerator), Decimal(denominator))

    def _ratio_decimal(self, numerator: Decimal, denominator: Decimal) -> Decimal:
        if denominator == 0:
            return _RATIO_ZERO
        return (numerator / denominator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _validate_date_range(self, *, date_from: date, date_to: date) -> None:
        if date_to < date_from:
            raise ServiceValidationError("date_to cannot be earlier than date_from.")
