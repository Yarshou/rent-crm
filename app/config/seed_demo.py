import asyncio
from datetime import date, timedelta
from decimal import Decimal

from config.security import create_password_hash
from config.settings import async_session_maker
from db.models import (
    Booking,
    BookingStatus,
    Car,
    CarPricingTier,
    CarStatus,
    DriveType,
    FuelType,
    InsurancePayment,
    MaintenanceRecord,
    MaintenanceSchedule,
    Organization,
    OrganizationMember,
    OrganizationRole,
    ServiceType,
    Transmission,
    User,
)
from sqlalchemy import select

DEMO_EMAIL = "demo@rent-crm.local"
DEMO_PASSWORD = "Password1!"
DEMO_ORGANIZATION = "Парк Восток"


async def get_or_create_user() -> User:
    async with async_session_maker() as session:
        user = await session.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                password_hash=create_password_hash(DEMO_PASSWORD),
                full_name="Demo User",
                is_super_admin=False,
            )
            session.add(user)
            await session.flush()
        await session.commit()
        return user


async def seed_demo() -> None:
    today = date.today()
    user = await get_or_create_user()

    async with async_session_maker() as session:
        organization = await session.scalar(select(Organization).where(Organization.name == DEMO_ORGANIZATION))
        if organization is None:
            organization = Organization(name=DEMO_ORGANIZATION)
            session.add(organization)
            await session.flush()

        membership = await session.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization.id,
                OrganizationMember.user_id == user.id,
            ),
        )
        if membership is None:
            session.add(
                OrganizationMember(
                    organization_id=organization.id,
                    user_id=user.id,
                    role=OrganizationRole.owner,
                ),
            )

        cars = {
            "DEMO-001": {
                "brand": "Toyota",
                "model": "Camry",
                "year": 2022,
                "status": CarStatus.rented,
                "mileage": 48_000,
                "city": "Tbilisi",
            },
            "DEMO-002": {
                "brand": "Hyundai",
                "model": "Tucson",
                "year": 2021,
                "status": CarStatus.available,
                "mileage": 61_000,
                "city": "Tbilisi",
            },
            "DEMO-003": {
                "brand": "Kia",
                "model": "K5",
                "year": 2023,
                "status": CarStatus.in_repair,
                "mileage": 24_000,
                "city": "Batumi",
            },
        }
        created_cars: dict[str, Car] = {}
        for license_plate, values in cars.items():
            car = await session.scalar(
                select(Car).where(
                    Car.organization_id == organization.id,
                    Car.license_plate == license_plate,
                ),
            )
            if car is None:
                car = Car(
                    organization_id=organization.id,
                    license_plate=license_plate,
                    vin=None,
                    drive_type=DriveType.fwd,
                    fuel_type=FuelType.petrol,
                    transmission=Transmission.automatic,
                    **values,
                )
                session.add(car)
                await session.flush()
            created_cars[license_plate] = car

            pricing_tier = await session.scalar(
                select(CarPricingTier).where(
                    CarPricingTier.car_id == car.id,
                    CarPricingTier.min_days == 1,
                ),
            )
            if pricing_tier is None:
                session.add(CarPricingTier(car_id=car.id, min_days=1, daily_rate=Decimal("75.00")))
                session.add(CarPricingTier(car_id=car.id, min_days=7, daily_rate=Decimal("65.00")))

        active_car = created_cars["DEMO-001"]
        available_car = created_cars["DEMO-002"]

        bookings = [
            (active_car, today - timedelta(days=1), today + timedelta(days=2), BookingStatus.active, "Nino Beridze"),
            (available_car, today + timedelta(days=3), today + timedelta(days=6), BookingStatus.planned, "Giorgi Kapanadze"),
            (available_car, today - timedelta(days=12), today - timedelta(days=9), BookingStatus.completed, "Anna Smith"),
        ]
        for car, start_date, end_date, status, renter_name in bookings:
            existing = await session.scalar(
                select(Booking).where(
                    Booking.organization_id == organization.id,
                    Booking.car_id == car.id,
                    Booking.start_date == start_date,
                    Booking.end_date == end_date,
                    Booking.renter_name == renter_name,
                ),
            )
            if existing is None:
                session.add(
                    Booking(
                        organization_id=organization.id,
                        car_id=car.id,
                        start_date=start_date,
                        end_date=end_date,
                        renter_name=renter_name,
                        renter_phone="+995555000000",
                        total_amount=Decimal("300.00"),
                        pickup_mileage=car.mileage if status == BookingStatus.active else None,
                        return_mileage=car.mileage + 450 if status == BookingStatus.completed else None,
                        status=status,
                        notes=None,
                    ),
                )

        maintenance_record = await session.scalar(
            select(MaintenanceRecord).where(
                MaintenanceRecord.organization_id == organization.id,
                MaintenanceRecord.car_id == created_cars["DEMO-003"].id,
                MaintenanceRecord.service_date == today - timedelta(days=2),
            ),
        )
        if maintenance_record is None:
            session.add(
                MaintenanceRecord(
                    organization_id=organization.id,
                    car_id=created_cars["DEMO-003"].id,
                    service_date=today - timedelta(days=2),
                    service_type=ServiceType.repair,
                    description="Suspension diagnostics and repair",
                    mileage_at_service=created_cars["DEMO-003"].mileage,
                    cost=Decimal("420.00"),
                    provider="Demo Service",
                ),
            )

        schedule = await session.scalar(
            select(MaintenanceSchedule).where(
                MaintenanceSchedule.organization_id == organization.id,
                MaintenanceSchedule.car_id == active_car.id,
                MaintenanceSchedule.service_type == ServiceType.oil_change,
                MaintenanceSchedule.is_completed.is_(False),
            ),
        )
        if schedule is None:
            session.add(
                MaintenanceSchedule(
                    organization_id=organization.id,
                    car_id=active_car.id,
                    service_type=ServiceType.oil_change,
                    scheduled_date=today + timedelta(days=14),
                    scheduled_mileage=None,
                    interval_km=10_000,
                    is_completed=False,
                    maintenance_record_id=None,
                ),
            )

        insurance = await session.scalar(
            select(InsurancePayment).where(
                InsurancePayment.organization_id == organization.id,
                InsurancePayment.car_id == active_car.id,
                InsurancePayment.payment_date == today.replace(day=1),
            ),
        )
        if insurance is None:
            session.add(
                InsurancePayment(
                    organization_id=organization.id,
                    car_id=active_car.id,
                    payment_date=today.replace(day=1),
                    period_start=today.replace(day=1),
                    period_end=today + timedelta(days=180),
                    amount=Decimal("180.00"),
                    provider="Demo Insurance",
                    notes=None,
                ),
            )

        await session.commit()

    print("Demo seed completed.")
    print(f"Email: {DEMO_EMAIL}")
    print(f"Password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed_demo())
