from http import HTTPMethod

from config.settings import settings
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from pydantic import BaseModel, HttpUrl, PositiveInt
from pydantic_settings import BaseSettings
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from uvicorn.middleware.message_logger import MessageLoggerMiddleware
from yaml import safe_load


class _CORSMiddlewareSettings(BaseModel):
    __class__ = CORSMiddleware
    allow_origins: list[HttpUrl]
    allow_methods: list[HTTPMethod]
    allow_headers: list[str]
    allow_credentials: bool
    expose_headers: list[str]
    max_age: PositiveInt


class MiddlewareSettings(BaseSettings):
    cors: _CORSMiddlewareSettings

    @classmethod
    def load(cls) -> "MiddlewareSettings":
        with open(settings.BASE_DIR / "config/config.yaml", encoding="utf-8") as file:
            return cls.model_validate(obj=safe_load(file), from_attributes=True)


def setup_middlewares(app: FastAPI, middleware_settings: MiddlewareSettings) -> None:
    for _, middleware in middleware_settings:
        app.add_middleware(middleware_class=middleware.__class__, **middleware.model_dump())
    app.add_middleware(middleware_class=MessageLoggerMiddleware)


def setup_docs(app: FastAPI) -> None:
    @app.get("/docs", include_in_schema=False)
    async def docs() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title="Rent CRM Documentation",
            swagger_ui_parameters={"tryItOutEnabled": "false"},
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title="Rent CRM Documentation",
            swagger_ui_parameters={"tryItOutEnabled": "false"},
        )


def setup(app: FastAPI) -> None:
    middleware_settings = MiddlewareSettings.load()
    setup_middlewares(app=app, middleware_settings=middleware_settings)
    setup_docs(app=app)
