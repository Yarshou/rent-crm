from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import Response
from fastapi.routing import APIRoute
from services import ServiceConflictError, ServiceNotFoundError, ServiceUnauthorizedError, ServiceValidationError

__all__ = ["ServiceErrorRoute"]


class ServiceErrorRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Any]:
        original_route_handler = super().get_route_handler()

        async def service_error_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except ServiceNotFoundError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except ServiceConflictError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            except ServiceUnauthorizedError as exc:
                raise HTTPException(
                    status_code=401,
                    detail=str(exc),
                    headers={"WWW-Authenticate": "Bearer"},
                ) from exc
            except ServiceValidationError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

        return service_error_route_handler
