from fastapi import APIRouter

from .details_routes import router as details_router
from .routes import router as cars_router

__all__ = ["router"]

router = APIRouter()
router.include_router(cars_router)
router.include_router(details_router)
