from api import v1
from fastapi import APIRouter

__all__ = [
    "router",
]
router = APIRouter(prefix="/api")
router.include_router(router=v1.router)
