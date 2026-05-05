from pydantic import BaseModel
from schemas.bookings.http import BookingResponse
from schemas.cars.http import CarPhotoResponse, CarPricingTierResponse, CarResponse
from schemas.insurance.http import InsurancePaymentResponse
from schemas.maintenance.http import MaintenanceRecordResponse, MaintenanceScheduleResponse

__all__ = ["CarDetailsResponse", "CarMaintenanceDetailsResponse"]


class CarMaintenanceDetailsResponse(BaseModel):
    records: list[MaintenanceRecordResponse]
    schedules: list[MaintenanceScheduleResponse]


class CarDetailsResponse(BaseModel):
    car: CarResponse
    photos: list[CarPhotoResponse]
    pricing_tiers: list[CarPricingTierResponse]
    active_booking: BookingResponse | None
    upcoming_bookings: list[BookingResponse]
    maintenance: CarMaintenanceDetailsResponse
    insurance: list[InsurancePaymentResponse]
