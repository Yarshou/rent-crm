from fastapi import APIRouter

from . import auth, bookings, calendar, cars, dashboard, insurance, maintenance, organizations, reports, search, users

__all__ = ["router"]

router = APIRouter(prefix="/v1")
router.include_router(auth.router)
router.include_router(organizations.router)
router.include_router(users.router)
router.include_router(cars.router)
router.include_router(bookings.router)
router.include_router(maintenance.router)
router.include_router(insurance.router)
router.include_router(dashboard.router)
router.include_router(calendar.router)
router.include_router(reports.router)
router.include_router(search.router)
