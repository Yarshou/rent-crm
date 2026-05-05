import asyncio
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from conftest import MockAsyncSession, MockExecuteResult
from db.models import (
    Booking,
    BookingStatus,
    Car,
    CarPhoto,
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
from repositories import (
    BookingRepository,
    CarPhotoRepository,
    CarPricingTierRepository,
    CarRepository,
    InsurancePaymentRepository,
    MaintenanceRecordRepository,
    MaintenanceScheduleRepository,
    OrganizationMemberRepository,
    OrganizationRepository,
    UnitOfWork,
    UserRepository,
)

BASE_TIME = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def run(coro):
    return asyncio.run(coro)


def created_at(offset: int = 0) -> datetime:
    return BASE_TIME + timedelta(minutes=offset)


def make_organization(name: str, *, offset: int = 0) -> Organization:
    return Organization(id=uuid4(), name=name, created_at=created_at(offset))


def make_user(email: str, *, offset: int = 0) -> User:
    return User(
        id=uuid4(),
        email=email,
        password_hash="hashed",
        full_name=email.split("@")[0].title(),
        is_super_admin=False,
        created_at=created_at(offset),
    )


def make_member(organization: Organization, user: User, *, offset: int = 0) -> OrganizationMember:
    return OrganizationMember(
        id=uuid4(),
        organization_id=organization.id,
        user_id=user.id,
        role=OrganizationRole.owner,
        created_at=created_at(offset),
    )


def make_car(
    organization: Organization,
    license_plate: str,
    *,
    brand: str = "Toyota",
    model: str = "Camry",
    city: str = "Tbilisi",
    status: CarStatus = CarStatus.available,
    mileage: int = 10_000,
    offset: int = 0,
) -> Car:
    return Car(
        id=uuid4(),
        organization_id=organization.id,
        brand=brand,
        model=model,
        year=2021,
        license_plate=license_plate,
        vin=None,
        drive_type=DriveType.fwd,
        fuel_type=FuelType.petrol,
        transmission=Transmission.automatic,
        mileage=mileage,
        city=city,
        status=status,
        created_at=created_at(offset),
    )


def make_booking(
    organization: Organization,
    car: Car,
    start_date: date,
    end_date: date,
    status: BookingStatus,
    *,
    offset: int = 0,
) -> Booking:
    return Booking(
        id=uuid4(),
        organization_id=organization.id,
        car_id=car.id,
        start_date=start_date,
        end_date=end_date,
        renter_name="Ivan Petrov",
        renter_phone="+995555000000",
        total_amount=Decimal("1000.00"),
        pickup_mileage=None,
        return_mileage=None,
        status=status,
        notes=None,
        created_at=created_at(offset),
    )


def test_base_repository_crud_methods(mock_session: MockAsyncSession) -> None:
    created = make_organization("Alpha")
    mock_session.get.return_value = created
    mock_session.set_execute_results(
        MockExecuteResult(scalars=[created]),
        MockExecuteResult(scalar=created),
        MockExecuteResult(rowcount=1),
        MockExecuteResult(rowcount=0),
    )

    async def scenario() -> None:
        repo = OrganizationRepository(mock_session)

        new_organization_dto = await repo.create(name="Created", created_at=created_at())
        assert new_organization_dto.name == "Created"

        organization_dto = await repo.get(created.id)
        assert organization_dto is not None
        assert organization_dto.id == created.id

        listed = await repo.list()
        assert [item.id for item in listed] == [created.id]

        updated = await repo.update(created.id, name="Beta")
        assert updated is not None
        assert updated.name == "Beta"

        by_name_dto = await repo.get_by_name("Beta")
        assert by_name_dto is not None
        assert by_name_dto.id == created.id

        assert await repo.delete_by_id(created.id) is True
        assert await repo.delete_by_id(created.id) is False

    run(scenario())

    mock_session.add.assert_called_once()
    # create + update each call flush(), so there are at least 2 flushes.
    assert mock_session.flush.await_count >= 2
    # session.get is used by base.get() and base.update().
    assert mock_session.get.await_count >= 2
    assert mock_session.execute.await_count == 4


def test_user_and_member_repository_queries(mock_session: MockAsyncSession) -> None:
    organization = make_organization("Fleet One")
    other_organization = make_organization("Fleet Two", offset=1)
    user = make_user("owner@example.com", offset=2)
    other_user = make_user("other@example.com", offset=3)
    member = make_member(organization, user, offset=4)
    other_member = make_member(other_organization, user, offset=5)

    mock_session.set_execute_results(
        MockExecuteResult(scalar=user),
        MockExecuteResult(scalar=None),
        MockExecuteResult(scalars=[member, other_member]),
        MockExecuteResult(scalars=[member]),
        MockExecuteResult(scalar=member),
        MockExecuteResult(scalar=member.id),
        MockExecuteResult(scalar=None),
    )

    async def scenario() -> None:
        users = UserRepository(mock_session)
        members = OrganizationMemberRepository(mock_session)

        found_user = await users.get_by_email("owner@example.com")
        assert found_user is not None
        assert found_user.id == user.id
        assert await users.get_by_email("missing@example.com") is None

        listed_by_user = await members.list_by_user(user.id)
        assert [item.id for item in listed_by_user] == [member.id, other_member.id]
        listed_by_org = await members.list_by_organization(organization.id)
        assert [item.id for item in listed_by_org] == [member.id]

        found_member = await members.get_by_user_and_organization(user_id=user.id, organization_id=organization.id)
        assert found_member is not None
        assert found_member.id == member.id

        assert await members.user_has_organization_access(user_id=user.id, organization_id=organization.id) is True
        assert await members.user_has_organization_access(user_id=other_user.id, organization_id=organization.id) is False

    run(scenario())

    assert mock_session.execute.await_count == 7


def test_organization_repository_lists_by_ids(mock_session: MockAsyncSession) -> None:
    first = make_organization("Bravo")
    second = make_organization("Alpha", offset=1)
    mock_session.set_execute_results(MockExecuteResult(scalars=[second, first]))

    async def scenario() -> None:
        repo = OrganizationRepository(mock_session)

        assert await repo.list_by_ids([]) == []
        listed = await repo.list_by_ids([first.id, second.id])
        assert [item.id for item in listed] == [second.id, first.id]

    run(scenario())

    mock_session.execute.assert_awaited_once()


def test_car_repository_filters_and_updates(mock_session: MockAsyncSession) -> None:
    organization = make_organization("Fleet")
    other_organization = make_organization("Other Fleet", offset=1)
    available_car = make_car(organization, "A001AA", brand="BMW", model="X3", city="Tbilisi", offset=2)
    rented_car = make_car(
        organization,
        "B002BB",
        brand="Audi",
        model="A4",
        city="Batumi",
        status=CarStatus.rented,
        offset=3,
    )

    mock_session.set_execute_results(
        MockExecuteResult(scalar=available_car),
        MockExecuteResult(scalar=None),
        MockExecuteResult(scalar=available_car),
        MockExecuteResult(scalars=[available_car]),
        MockExecuteResult(scalars=[rented_car]),
        MockExecuteResult(scalars=[available_car]),
    )
    mock_session.get.return_value = available_car

    async def scenario() -> None:
        repo = CarRepository(mock_session)

        first = await repo.get_for_organization(organization_id=organization.id, car_id=available_car.id)
        assert first is not None
        assert first.id == available_car.id
        assert await repo.get_for_organization(organization_id=other_organization.id, car_id=available_car.id) is None

        by_plate = await repo.get_by_license_plate(organization_id=organization.id, license_plate="A001AA")
        assert by_plate is not None
        assert by_plate.id == available_car.id

        assert await repo.list_by_ids_for_organization(organization_id=organization.id, car_ids=[]) == []
        listed = await repo.list_by_ids_for_organization(
            organization_id=organization.id,
            car_ids=[available_car.id],
        )
        assert [item.id for item in listed] == [available_car.id]

        rented = await repo.list_for_organization(organization.id, statuses=[CarStatus.rented])
        assert [item.id for item in rented] == [rented_car.id]
        in_tbilisi = await repo.list_for_organization(organization.id, city="Tbilisi")
        assert [item.id for item in in_tbilisi] == [available_car.id]

        updated_status = await repo.set_status(available_car.id, CarStatus.in_repair)
        assert updated_status is not None
        assert updated_status.status == CarStatus.in_repair
        updated_mileage = await repo.update_mileage(available_car.id, 12_500)
        assert updated_mileage is not None
        assert updated_mileage.mileage == 12_500

    run(scenario())

    assert mock_session.execute.await_count == 6


def test_car_photo_and_pricing_repository_queries(mock_session: MockAsyncSession) -> None:
    organization = make_organization("Fleet")
    car = make_car(organization, "A001AA")
    first_photo = CarPhoto(id=uuid4(), car_id=car.id, file_path="/cars/front.jpg", position=2, created_at=created_at(1))
    second_photo = CarPhoto(id=uuid4(), car_id=car.id, file_path="/cars/side.jpg", position=1, created_at=created_at(2))
    one_day = CarPricingTier(
        id=uuid4(),
        car_id=car.id,
        min_days=1,
        daily_rate=Decimal("200.00"),
        created_at=created_at(3),
    )
    three_days = CarPricingTier(
        id=uuid4(),
        car_id=car.id,
        min_days=3,
        daily_rate=Decimal("170.00"),
        created_at=created_at(4),
    )
    seven_days = CarPricingTier(
        id=uuid4(),
        car_id=car.id,
        min_days=7,
        daily_rate=Decimal("150.00"),
        created_at=created_at(5),
    )

    mock_session.set_execute_results(
        MockExecuteResult(scalars=[second_photo, first_photo]),
        MockExecuteResult(scalars=[one_day, three_days, seven_days]),
        MockExecuteResult(scalar=three_days),
        MockExecuteResult(scalar=three_days),
        MockExecuteResult(rowcount=2),
        MockExecuteResult(rowcount=3),
    )
    mock_session.get.return_value = three_days

    async def scenario() -> None:
        photos = CarPhotoRepository(mock_session)
        pricing = CarPricingTierRepository(mock_session)

        listed_photos = await photos.list_for_car(car.id)
        assert [item.id for item in listed_photos] == [second_photo.id, first_photo.id]

        listed_tiers = await pricing.list_for_car(car.id)
        assert [item.min_days for item in listed_tiers] == [1, 3, 7]

        by_min = await pricing.get_by_min_days(car_id=car.id, min_days=3)
        assert by_min is not None
        assert by_min.id == three_days.id

        applicable = await pricing.get_applicable_for_duration(car_id=car.id, rental_days=5)
        assert applicable is not None
        assert applicable.id == three_days.id

        updated = await pricing.set_daily_rate(three_days.id, Decimal("160.00"))
        assert updated is not None
        assert updated.daily_rate == Decimal("160.00")

        assert await photos.delete_for_car(car.id) == 2
        assert await pricing.delete_for_car(car.id) == 3

    run(scenario())

    assert mock_session.execute.await_count == 6


def test_booking_repository_calendar_filters_and_overlap(mock_session: MockAsyncSession) -> None:
    organization = make_organization("Fleet")
    other_organization = make_organization("Other Fleet", offset=1)
    car = make_car(organization, "A001AA", offset=2)
    other_car = make_car(organization, "B002BB", offset=3)
    planned = make_booking(organization, car, date(2026, 1, 5), date(2026, 1, 10), BookingStatus.planned, offset=5)
    active = make_booking(organization, car, date(2026, 1, 15), date(2026, 1, 20), BookingStatus.active, offset=6)
    other_car_booking = make_booking(
        organization,
        other_car,
        date(2026, 1, 7),
        date(2026, 1, 9),
        BookingStatus.planned,
        offset=8,
    )

    mock_session.set_execute_results(
        MockExecuteResult(scalar=planned),
        MockExecuteResult(scalar=None),
        MockExecuteResult(scalars=[planned, other_car_booking, active]),
        MockExecuteResult(scalars=[active]),
        MockExecuteResult(scalars=[planned]),
        MockExecuteResult(scalar=None),
        MockExecuteResult(scalar=1),
    )

    async def scenario() -> None:
        repo = BookingRepository(mock_session)

        first = await repo.get_for_organization(organization_id=organization.id, booking_id=planned.id)
        assert first is not None
        assert first.id == planned.id
        assert await repo.get_for_organization(organization_id=other_organization.id, booking_id=planned.id) is None

        listed = await repo.list_for_organization(
            organization.id,
            statuses=[BookingStatus.planned, BookingStatus.active],
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
        )
        assert [item.id for item in listed] == [planned.id, other_car_booking.id, active.id]

        active_for_car = await repo.list_active_for_car(organization_id=organization.id, car_id=car.id)
        assert [item.id for item in active_for_car] == [active.id]

        overlapping = await repo.find_overlapping(
            organization_id=organization.id,
            car_id=car.id,
            start_date=date(2026, 1, 8),
            end_date=date(2026, 1, 11),
        )
        assert [item.id for item in overlapping] == [planned.id]

        assert (
            await repo.has_overlapping_booking(
                organization_id=organization.id,
                car_id=car.id,
                start_date=date(2026, 1, 8),
                end_date=date(2026, 1, 11),
                exclude_booking_id=planned.id,
            )
            is False
        )
        assert await repo.count_active_for_car(organization_id=organization.id, car_id=car.id) == 1

    run(scenario())

    assert mock_session.execute.await_count == 7


def test_maintenance_repositories_filters_and_due_queries(mock_session: MockAsyncSession) -> None:
    organization = make_organization("Fleet")
    car = make_car(organization, "A001AA", offset=1)
    oil_record = MaintenanceRecord(
        id=uuid4(),
        organization_id=organization.id,
        car_id=car.id,
        service_date=date(2026, 1, 10),
        service_type=ServiceType.oil_change,
        description="Oil changed",
        mileage_at_service=11_000,
        cost=Decimal("120.00"),
        provider="Service A",
        created_at=created_at(2),
    )
    tire_record = MaintenanceRecord(
        id=uuid4(),
        organization_id=organization.id,
        car_id=car.id,
        service_date=date(2026, 2, 10),
        service_type=ServiceType.tires,
        description="Tires changed",
        mileage_at_service=12_000,
        cost=Decimal("300.00"),
        provider="Service B",
        created_at=created_at(3),
    )
    due_by_date = MaintenanceSchedule(
        id=uuid4(),
        organization_id=organization.id,
        car_id=car.id,
        service_type=ServiceType.oil_change,
        scheduled_date=date(2026, 1, 15),
        scheduled_mileage=None,
        interval_km=10_000,
        is_completed=False,
        maintenance_record_id=None,
        created_at=created_at(4),
    )
    due_by_mileage = MaintenanceSchedule(
        id=uuid4(),
        organization_id=organization.id,
        car_id=car.id,
        service_type=ServiceType.brakes,
        scheduled_date=None,
        scheduled_mileage=12_500,
        interval_km=None,
        is_completed=False,
        maintenance_record_id=None,
        created_at=created_at(5),
    )

    mock_session.set_execute_results(
        MockExecuteResult(scalar=oil_record),
        MockExecuteResult(scalars=[tire_record]),
        MockExecuteResult(scalars=[oil_record]),
        MockExecuteResult(scalar=due_by_date),
        MockExecuteResult(scalars=[due_by_date, due_by_mileage]),
        MockExecuteResult(scalars=[due_by_date]),
        MockExecuteResult(scalars=[due_by_mileage]),
    )

    async def scenario() -> None:
        records = MaintenanceRecordRepository(mock_session)
        schedules = MaintenanceScheduleRepository(mock_session)

        first = await records.get_for_organization(
            organization_id=organization.id,
            maintenance_record_id=oil_record.id,
        )
        assert first is not None
        assert first.id == oil_record.id

        for_car = await records.list_for_car(
            organization_id=organization.id,
            car_id=car.id,
            service_types=[ServiceType.tires],
        )
        assert [item.id for item in for_car] == [tire_record.id]

        for_org = await records.list_for_organization(
            organization.id,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
        )
        assert [item.id for item in for_org] == [oil_record.id]

        first_schedule = await schedules.get_for_organization(
            organization_id=organization.id,
            maintenance_schedule_id=due_by_date.id,
        )
        assert first_schedule is not None
        assert first_schedule.id == due_by_date.id

        open_for_car = await schedules.list_open_for_car(organization_id=organization.id, car_id=car.id)
        assert [item.id for item in open_for_car] == [due_by_date.id, due_by_mileage.id]

        date_due = await schedules.list_due_by_date(organization_id=organization.id, due_date=date(2026, 1, 31))
        assert [item.id for item in date_due] == [due_by_date.id]

        mileage_due = await schedules.list_due_by_mileage(
            organization_id=organization.id,
            car_id=car.id,
            mileage=13_000,
        )
        assert [item.id for item in mileage_due] == [due_by_mileage.id]

    run(scenario())

    assert mock_session.execute.await_count == 7


def test_insurance_payment_repository_filters_coverage_and_active_date(mock_session: MockAsyncSession) -> None:
    organization = make_organization("Fleet")
    other_organization = make_organization("Other Fleet", offset=1)
    car = make_car(organization, "A001AA", offset=2)
    january = InsurancePayment(
        id=uuid4(),
        organization_id=organization.id,
        car_id=car.id,
        payment_date=date(2026, 1, 1),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        amount=Decimal("500.00"),
        provider="Provider A",
        notes=None,
        created_at=created_at(4),
    )
    february = InsurancePayment(
        id=uuid4(),
        organization_id=organization.id,
        car_id=car.id,
        payment_date=date(2026, 2, 1),
        period_start=date(2026, 2, 1),
        period_end=date(2026, 2, 28),
        amount=Decimal("500.00"),
        provider="Provider A",
        notes=None,
        created_at=created_at(5),
    )

    mock_session.set_execute_results(
        MockExecuteResult(scalar=january),
        MockExecuteResult(scalar=None),
        MockExecuteResult(scalars=[january]),
        MockExecuteResult(scalars=[february]),
        MockExecuteResult(scalars=[january]),
    )

    async def scenario() -> None:
        repo = InsurancePaymentRepository(mock_session)

        first = await repo.get_for_organization(
            organization_id=organization.id,
            insurance_payment_id=january.id,
        )
        assert first is not None
        assert first.id == january.id
        assert (
            await repo.get_for_organization(
                organization_id=other_organization.id,
                insurance_payment_id=january.id,
            )
            is None
        )

        for_car = await repo.list_for_car(
            organization_id=organization.id,
            car_id=car.id,
            coverage_from=date(2026, 1, 15),
            coverage_to=date(2026, 1, 20),
        )
        assert [item.id for item in for_car] == [january.id]

        for_org = await repo.list_for_organization(
            organization.id,
            payment_date_from=date(2026, 2, 1),
            payment_date_to=date(2026, 2, 28),
        )
        assert [item.id for item in for_org] == [february.id]

        active = await repo.list_active_on_date(
            organization_id=organization.id,
            target_date=date(2026, 1, 15),
        )
        assert [item.id for item in active] == [january.id]

    run(scenario())

    assert mock_session.execute.await_count == 5


def _consume_uuid(_: UUID) -> None:
    """Touch UUID so unused-imports linters stay happy."""


def test_unit_of_work_exposes_repositories_and_controls_transactions() -> None:
    committed_session = MockAsyncSession()
    rollback_session = MockAsyncSession()
    sessions = [committed_session, rollback_session]

    def session_factory() -> MockAsyncSession:
        return sessions.pop(0)

    async def scenario() -> None:
        async with UnitOfWork(session_factory) as uow:
            assert isinstance(uow.organizations, OrganizationRepository)
            assert isinstance(uow.users, UserRepository)
            assert isinstance(uow.organization_members, OrganizationMemberRepository)
            assert isinstance(uow.cars, CarRepository)
            assert isinstance(uow.car_photos, CarPhotoRepository)
            assert isinstance(uow.car_pricing_tiers, CarPricingTierRepository)
            assert isinstance(uow.bookings, BookingRepository)
            assert isinstance(uow.maintenance_records, MaintenanceRecordRepository)
            assert isinstance(uow.maintenance_schedules, MaintenanceScheduleRepository)
            assert isinstance(uow.insurance_payments, InsurancePaymentRepository)

            await uow.organizations.create(name="Committed", created_at=created_at())
            await uow.commit()

        try:
            async with UnitOfWork(session_factory) as uow:
                await uow.organizations.create(name="Rolled Back", created_at=created_at(1))
                raise RuntimeError("rollback")
        except RuntimeError:
            pass

    run(scenario())

    committed_session.add.assert_called_once()
    committed_session.commit.assert_awaited_once()
    committed_session.rollback.assert_not_awaited()
    committed_session.close.assert_awaited_once()

    rollback_session.add.assert_called_once()
    rollback_session.commit.assert_not_awaited()
    rollback_session.rollback.assert_awaited_once()
    rollback_session.close.assert_awaited_once()
