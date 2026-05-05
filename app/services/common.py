from collections.abc import Callable

from repositories import UnitOfWork

__all__ = [
    "ServiceConflictError",
    "ServiceError",
    "ServiceNotFoundError",
    "ServiceUnauthorizedError",
    "ServiceValidationError",
    "UnitOfWorkFactory",
]

UnitOfWorkFactory = Callable[[], UnitOfWork]


class ServiceError(Exception):
    pass


class ServiceNotFoundError(ServiceError):
    pass


class ServiceUnauthorizedError(ServiceError):
    pass


class ServiceValidationError(ServiceError):
    pass


class ServiceConflictError(ServiceError):
    pass
