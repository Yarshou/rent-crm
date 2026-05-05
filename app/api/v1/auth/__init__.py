from fastapi import APIRouter

from .routes import router as auth_router

__all__ = [
    "router",
]


router = APIRouter()
router.include_router(router=auth_router)
