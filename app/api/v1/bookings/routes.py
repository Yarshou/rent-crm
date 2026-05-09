from datetime import date
from typing import Annotated
from uuid import UUID

from api.dependencies import get_booking_service, get_current_organization
from api.routing import ServiceErrorRoute
from db.models import BookingStatus
from fastapi import APIRouter, Depends, Query, Response, status
from schemas import (
    AmountResponse,
    BookingActivateInput,
    BookingActivateRequest,
    BookingCancelInput,
    BookingCompleteInput,
    BookingCompleteRequest,
    BookingCreateInput,
    BookingCreateRequest,
    BookingDeleteInput,
    BookingGetInput,
    BookingListInput,
    BookingRescheduleInput,
    BookingRescheduleRequest,
    BookingResponse,
    BookingTotalInput,
    BookingTotalRequest,
    BookingUpdateDetailsInput,
    BookingUpdateDetailsRequest,
    OrganizationDTO,
)
from services import BookingService

__all__ = ["router"]

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
    route_class=ServiceErrorRoute,
)


@router.get("", response_model=list[BookingResponse])
async def list_bookings(
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[BookingService, Depends(get_booking_service)],
    car_ids: Annotated[list[UUID] | None, Query()] = None,
    statuses: Annotated[list[BookingStatus] | None, Query()] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> list[BookingResponse]:
    bookings = await service.list(
        BookingListInput(
            organization_id=organization.id,
            car_ids=car_ids,
            statuses=statuses,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=limit,
        ),
    )
    return [BookingResponse.model_validate(booking) for booking in bookings]


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingResponse:
    booking = await service.create(
        BookingCreateInput(
            organization_id=organization.id,
            car_id=payload.car_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            renter_name=payload.renter_name,
            renter_phone=payload.renter_phone,
            total_amount=payload.total_amount,
            currency=payload.currency,
            notes=payload.notes,
        ),
    )
    return BookingResponse.model_validate(booking)


@router.post("/calculate-total", response_model=AmountResponse)
async def calculate_booking_total(
    payload: BookingTotalRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> AmountResponse:
    total_amount, currency = await service.calculate_total_amount(
        BookingTotalInput(
            organization_id=organization.id,
            car_id=payload.car_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
        ),
    )
    return AmountResponse(total_amount=total_amount, currency=currency)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingResponse:
    booking = await service.get(BookingGetInput(organization_id=organization.id, booking_id=booking_id))
    return BookingResponse.model_validate(booking)


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking_details(
    booking_id: UUID,
    payload: BookingUpdateDetailsRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingResponse:
    booking = await service.update_details(
        BookingUpdateDetailsInput(
            organization_id=organization.id,
            booking_id=booking_id,
            **payload.model_dump(exclude_unset=True),
        ),
    )
    return BookingResponse.model_validate(booking)


@router.put("/{booking_id}/schedule", response_model=BookingResponse)
async def reschedule_booking(
    booking_id: UUID,
    payload: BookingRescheduleRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingResponse:
    booking = await service.reschedule(
        BookingRescheduleInput(
            organization_id=organization.id,
            booking_id=booking_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            car_id=payload.car_id,
            total_amount=payload.total_amount,
            currency=payload.currency,
            recalculate_total=payload.recalculate_total,
        ),
    )
    return BookingResponse.model_validate(booking)


@router.post("/{booking_id}/activate", response_model=BookingResponse)
async def activate_booking(
    booking_id: UUID,
    payload: BookingActivateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingResponse:
    booking = await service.activate(
        BookingActivateInput(
            organization_id=organization.id,
            booking_id=booking_id,
            pickup_mileage=payload.pickup_mileage,
        ),
    )
    return BookingResponse.model_validate(booking)


@router.post("/{booking_id}/complete", response_model=BookingResponse)
async def complete_booking(
    booking_id: UUID,
    payload: BookingCompleteRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingResponse:
    booking = await service.complete(
        BookingCompleteInput(
            organization_id=organization.id,
            booking_id=booking_id,
            return_mileage=payload.return_mileage,
        ),
    )
    return BookingResponse.model_validate(booking)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingResponse:
    booking = await service.cancel(BookingCancelInput(organization_id=organization.id, booking_id=booking_id))
    return BookingResponse.model_validate(booking)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> Response:
    await service.delete(BookingDeleteInput(organization_id=organization.id, booking_id=booking_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
