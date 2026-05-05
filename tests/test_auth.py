import asyncio
import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("APP_PORT", "8000")
os.environ.setdefault("POSTGRES_DB", "rent_crm")
os.environ.setdefault("POSTGRES_HOST", "postgres")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("JWT_ACCESS_SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_ACCESS_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_EXPIRE", "15m")
os.environ.setdefault("JWT_REFRESH_ALGORITHM", "HS256")
os.environ.setdefault("JWT_REFRESH_EXPIRE", "7d")

from api.dependencies import get_current_user
from api.v1.auth.routes import get_me, login_user, register_user
from config.security import (
    create_access_token,
    create_password_hash,
    create_refresh_token,
    decode_access_token,
    verify_password,
)
from db.models import User
from schemas import (
    LoginRequest,
    OrganizationDTO,
    RegisterUserRequest,
    UserAuthenticateInput,
    UserByEmailInput,
    UserCreateInput,
    UserDTO,
    UserGetInput,
    UserListOrganizationsInput,
    UserRegisterInput,
)
from services import ServiceConflictError, ServiceNotFoundError, ServiceUnauthorizedError, UserService


def run(coro):
    return asyncio.run(coro)


def make_user_dto(email: str = "user@example.com", password: str = "Password1!") -> UserDTO:
    return UserDTO(
        id=uuid4(),
        email=email,
        password_hash=create_password_hash(password),
        full_name="Test User",
        is_super_admin=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class FakeUsersRepository:
    def __init__(self, users: list[UserDTO] | None = None) -> None:
        self.users_by_email: dict[str, User] = {}
        for user in users or []:
            self.users_by_email[user.email] = User(
                id=user.id,
                email=user.email,
                password_hash=user.password_hash,
                full_name=user.full_name,
                is_super_admin=user.is_super_admin,
                created_at=user.created_at,
            )
        self.flushed = False

    async def get(self, user_id: UUID) -> UserDTO | None:
        for user in self.users_by_email.values():
            if user.id == user_id:
                return UserDTO.model_validate(user)
        return None

    async def get_by_email(self, email: str) -> UserDTO | None:
        user = self.users_by_email.get(email)
        return UserDTO.model_validate(user) if user is not None else None

    async def create(self, **values) -> UserDTO:
        user = User(id=uuid4(), created_at=datetime(2026, 1, 1, tzinfo=UTC), **values)
        self.users_by_email[user.email] = user
        return UserDTO.model_validate(user)

    async def flush(self) -> None:
        self.flushed = True


class FakeUnitOfWork:
    def __init__(self, users: FakeUsersRepository) -> None:
        self.users = users
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


class StubUserService:
    def __init__(self, user: UserDTO | None = None) -> None:
        self.user = user

    async def register(self, input: UserRegisterInput) -> UserDTO:
        if self.user is not None:
            raise ServiceConflictError("User with this email already exists.")

        self.user = UserDTO(
            id=uuid4(),
            email=input.email,
            password_hash=create_password_hash(input.password),
            full_name=input.full_name,
            is_super_admin=False,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        return self.user

    async def create(self, input: UserCreateInput) -> UserDTO:
        return await self.register(
            UserRegisterInput(email=input.email, password="Password1!", full_name=input.full_name),
        )

    async def authenticate(self, input: UserAuthenticateInput) -> UserDTO:
        if (
            self.user is None
            or self.user.email != input.email
            or not verify_password(input.password, self.user.password_hash)
        ):
            raise ServiceUnauthorizedError("Invalid email or password.")
        return self.user

    async def get(self, input: UserGetInput) -> UserDTO:
        if self.user is not None and self.user.id == input.user_id:
            return self.user
        raise ServiceNotFoundError("User not found.")

    async def get_by_email(self, input: UserByEmailInput) -> UserDTO:
        if self.user is not None and self.user.email == input.email:
            return self.user
        raise ServiceNotFoundError("User not found.")

    async def list_organizations(self, input: UserListOrganizationsInput) -> list[OrganizationDTO]:
        organization = OrganizationDTO(
            id=uuid4(),
            name="Парк Восток",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        organizations = [organization]
        if input.limit is None:
            return organizations[input.offset :]
        return organizations[input.offset : input.offset + input.limit]


def test_password_hash_round_trip() -> None:
    password_hash = create_password_hash("Password1!")

    assert password_hash != "Password1!"
    assert verify_password("Password1!", password_hash)
    assert not verify_password("Password2!", password_hash)


def test_access_token_round_trip_and_refresh_rejection() -> None:
    user = make_user_dto()

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    payload = decode_access_token(access_token)

    assert payload.sub == str(user.id)
    assert payload.role == "user"

    with pytest.raises(HTTPException) as exception_info:
        decode_access_token(refresh_token)

    assert exception_info.value.status_code == 401


def test_user_service_register_hashes_password_and_commits() -> None:
    async def scenario() -> None:
        repository = FakeUsersRepository()
        uow = FakeUnitOfWork(repository)
        service = UserService(lambda: uow)

        user = await service.register(
            UserRegisterInput(email="new@example.com", password="Password1!", full_name="New User"),
        )

        assert user.email == "new@example.com"
        assert user.password_hash != "Password1!"
        assert verify_password("Password1!", user.password_hash)
        assert user.is_super_admin is False
        assert uow.committed is True

    run(scenario())


def test_user_service_register_rejects_duplicate_email() -> None:
    async def scenario() -> None:
        existing_user = make_user_dto()
        uow = FakeUnitOfWork(FakeUsersRepository([existing_user]))
        service = UserService(lambda: uow)

        with pytest.raises(ServiceConflictError):
            await service.register(
                UserRegisterInput(email=existing_user.email, password="Password1!", full_name="Duplicate User"),
            )

    run(scenario())


def test_user_service_authenticate() -> None:
    async def scenario() -> None:
        user = make_user_dto(password="Password1!")
        service = UserService(lambda: FakeUnitOfWork(FakeUsersRepository([user])))

        authenticated = await service.authenticate(
            UserAuthenticateInput(email=user.email, password="Password1!"),
        )

        assert authenticated.id == user.id

        with pytest.raises(ServiceUnauthorizedError):
            await service.authenticate(
                UserAuthenticateInput(email=user.email, password="WrongPassword1!"),
            )

    run(scenario())


def test_auth_routes_issue_tokens_and_return_current_user() -> None:
    async def scenario() -> None:
        service = StubUserService()
        register_response = await register_user(
            payload=RegisterUserRequest(
                email="route@example.com",
                password="Password1!",
                confirm_password="Password1!",
                full_name="Route User",
            ),
            service=service,
        )

        assert register_response.token_type == "bearer"
        assert register_response.access_token
        assert register_response.refresh_token

        login_response = await login_user(
            payload=LoginRequest(email="route@example.com", password="Password1!"),
            service=service,
        )
        assert login_response.access_token

        current_user = await get_current_user(
            credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=login_response.access_token),
            user_service=service,
        )
        me = await get_me(current_user=current_user, service=service)

        assert service.user is not None
        assert me.id == service.user.id
        assert me.email == "route@example.com"
        assert me.organization is not None
        assert me.organization.name == "Парк Восток"

    run(scenario())


def test_current_user_rejects_missing_or_invalid_token() -> None:
    async def scenario() -> None:
        with pytest.raises(HTTPException) as missing_exception:
            await get_current_user(credentials=None, user_service=StubUserService())
        assert missing_exception.value.status_code == 401

        with pytest.raises(HTTPException) as invalid_exception:
            await get_current_user(
                credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.value"),
                user_service=StubUserService(),
            )
        assert invalid_exception.value.status_code == 401

    run(scenario())
