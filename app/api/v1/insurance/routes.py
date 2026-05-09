from datetime import date
from typing import Annotated
from uuid import UUID

from api.dependencies import get_current_organization, get_insurance_service
from api.routing import ServiceErrorRoute
from fastapi import APIRouter, Depends, Query, Response, status
from schemas import (
    InsurancePaymentActiveOnDateInput,
    InsurancePaymentCreateInput,
    InsurancePaymentCreateRequest,
    InsurancePaymentDeleteInput,
    InsurancePaymentGetInput,
    InsurancePaymentListForCarInput,
    InsurancePaymentListInput,
    InsurancePaymentResponse,
    InsurancePaymentUpdateInput,
    InsurancePaymentUpdateRequest,
    OrganizationDTO,
)
from services import InsuranceService

__all__ = ["router"]

router = APIRouter(
    prefix="/insurance-payments",
    tags=["insurance"],
    route_class=ServiceErrorRoute,
)


@router.get("", response_model=list[InsurancePaymentResponse])
async def list_insurance_payments(
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[InsuranceService, Depends(get_insurance_service)],
    car_ids: Annotated[list[UUID] | None, Query()] = None,
    payment_date_from: date | None = None,
    payment_date_to: date | None = None,
    coverage_from: date | None = None,
    coverage_to: date | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> list[InsurancePaymentResponse]:
    payments = await service.list(
        InsurancePaymentListInput(
            organization_id=organization.id,
            car_ids=car_ids,
            payment_date_from=payment_date_from,
            payment_date_to=payment_date_to,
            coverage_from=coverage_from,
            coverage_to=coverage_to,
            offset=offset,
            limit=limit,
        ),
    )
    return [InsurancePaymentResponse.model_validate(payment) for payment in payments]


@router.post("", response_model=InsurancePaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_insurance_payment(
    payload: InsurancePaymentCreateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[InsuranceService, Depends(get_insurance_service)],
) -> InsurancePaymentResponse:
    payment = await service.create(
        InsurancePaymentCreateInput(
            organization_id=organization.id,
            car_id=payload.car_id,
            payment_date=payload.payment_date,
            period_start=payload.period_start,
            period_end=payload.period_end,
            amount=payload.amount,
            currency=payload.currency,
            provider=payload.provider,
            notes=payload.notes,
        ),
    )
    return InsurancePaymentResponse.model_validate(payment)


@router.get("/active", response_model=list[InsurancePaymentResponse])
async def list_active_insurance_payments(
    target_date: date,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[InsuranceService, Depends(get_insurance_service)],
) -> list[InsurancePaymentResponse]:
    payments = await service.list_active_on_date(
        InsurancePaymentActiveOnDateInput(organization_id=organization.id, target_date=target_date),
    )
    return [InsurancePaymentResponse.model_validate(payment) for payment in payments]


@router.get("/cars/{car_id}", response_model=list[InsurancePaymentResponse])
async def list_car_insurance_payments(
    car_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[InsuranceService, Depends(get_insurance_service)],
    coverage_from: date | None = None,
    coverage_to: date | None = None,
) -> list[InsurancePaymentResponse]:
    payments = await service.list_for_car(
        InsurancePaymentListForCarInput(
            organization_id=organization.id,
            car_id=car_id,
            coverage_from=coverage_from,
            coverage_to=coverage_to,
        ),
    )
    return [InsurancePaymentResponse.model_validate(payment) for payment in payments]


@router.get("/{insurance_payment_id}", response_model=InsurancePaymentResponse)
async def get_insurance_payment(
    insurance_payment_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[InsuranceService, Depends(get_insurance_service)],
) -> InsurancePaymentResponse:
    payment = await service.get(
        InsurancePaymentGetInput(organization_id=organization.id, insurance_payment_id=insurance_payment_id),
    )
    return InsurancePaymentResponse.model_validate(payment)


@router.patch("/{insurance_payment_id}", response_model=InsurancePaymentResponse)
async def update_insurance_payment(
    insurance_payment_id: UUID,
    payload: InsurancePaymentUpdateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[InsuranceService, Depends(get_insurance_service)],
) -> InsurancePaymentResponse:
    payment = await service.update(
        InsurancePaymentUpdateInput(
            organization_id=organization.id,
            insurance_payment_id=insurance_payment_id,
            **payload.model_dump(exclude_unset=True),
        ),
    )
    return InsurancePaymentResponse.model_validate(payment)


@router.delete("/{insurance_payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insurance_payment(
    insurance_payment_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[InsuranceService, Depends(get_insurance_service)],
) -> Response:
    await service.delete(
        InsurancePaymentDeleteInput(organization_id=organization.id, insurance_payment_id=insurance_payment_id),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
