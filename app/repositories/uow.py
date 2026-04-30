from collections.abc import Callable
from types import TracebackType

from repositories.bookings import BookingRepository
from repositories.cars import CarPhotoRepository, CarPricingTierRepository, CarRepository
from repositories.insurance import InsurancePaymentRepository
from repositories.maintenance import MaintenanceRecordRepository, MaintenanceScheduleRepository
from repositories.organizations import OrganizationRepository
from repositories.users import OrganizationMemberRepository, UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["UnitOfWork"]


class UnitOfWork:
    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork must be entered before using the session.")
        return self._session

    async def __aenter__(self) -> "UnitOfWork":
        self._session = self._session_factory()
        self.organizations = OrganizationRepository(self.session)
        self.users = UserRepository(self.session)
        self.organization_members = OrganizationMemberRepository(self.session)
        self.cars = CarRepository(self.session)
        self.car_photos = CarPhotoRepository(self.session)
        self.car_pricing_tiers = CarPricingTierRepository(self.session)
        self.bookings = BookingRepository(self.session)
        self.maintenance_records = MaintenanceRecordRepository(self.session)
        self.maintenance_schedules = MaintenanceScheduleRepository(self.session)
        self.insurance_payments = InsurancePaymentRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            await self.session.close()
            self._session = None

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
