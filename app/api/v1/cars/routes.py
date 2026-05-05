from typing import Annotated
from uuid import UUID

from api.dependencies import get_car_service, get_current_organization
from api.routing import ServiceErrorRoute
from db.models import CarStatus
from fastapi import APIRouter, Depends, Query, Request, Response, status
from schemas import (
    CarCreateInput,
    CarCreateRequest,
    CarDeleteInput,
    CarGetInput,
    CarListInput,
    CarPhotoInput,
    CarPhotoRequest,
    CarPhotoResponse,
    CarPhotosListInput,
    CarPhotosReplaceInput,
    CarPhotoUploadInput,
    CarPricingTierInput,
    CarPricingTierRequest,
    CarPricingTierResponse,
    CarPricingTiersListInput,
    CarPricingTiersReplaceInput,
    CarResponse,
    CarStatusUpdateInput,
    CarStatusUpdateRequest,
    CarUpdateInput,
    CarUpdateRequest,
    OrganizationDTO,
)
from services import CarService

__all__ = ["router"]

router = APIRouter(
    prefix="/cars",
    tags=["cars"],
    route_class=ServiceErrorRoute,
)


@router.get("", response_model=list[CarResponse])
async def list_cars(
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[CarService, Depends(get_car_service)],
    statuses: Annotated[list[CarStatus] | None, Query()] = None,
    city: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> list[CarResponse]:
    cars = await service.list(
        CarListInput(
            organization_id=organization.id,
            statuses=statuses,
            city=city,
            offset=offset,
            limit=limit,
        ),
    )
    return [CarResponse.model_validate(car) for car in cars]


@router.post("", response_model=CarResponse, status_code=status.HTTP_201_CREATED)
async def create_car(
    payload: CarCreateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[CarService, Depends(get_car_service)],
) -> CarResponse:
    car = await service.create(
        CarCreateInput(
            organization_id=organization.id,
            brand=payload.brand,
            model=payload.model,
            year=payload.year,
            license_plate=payload.license_plate,
            vin=payload.vin,
            drive_type=payload.drive_type,
            fuel_type=payload.fuel_type,
            transmission=payload.transmission,
            mileage=payload.mileage,
            city=payload.city,
            status=payload.status,
            photos=[CarPhotoInput(**photo.model_dump()) for photo in payload.photos],
            pricing_tiers=[CarPricingTierInput(**tier.model_dump()) for tier in payload.pricing_tiers],
        ),
    )
    return CarResponse.model_validate(car)


@router.get("/{car_id}", response_model=CarResponse)
async def get_car(
    car_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[CarService, Depends(get_car_service)],
) -> CarResponse:
    car = await service.get(CarGetInput(organization_id=organization.id, car_id=car_id))
    return CarResponse.model_validate(car)


@router.patch("/{car_id}", response_model=CarResponse)
async def update_car(
    car_id: UUID,
    payload: CarUpdateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[CarService, Depends(get_car_service)],
) -> CarResponse:
    car = await service.update(
        CarUpdateInput(
            organization_id=organization.id,
            car_id=car_id,
            **payload.model_dump(exclude_unset=True),
        ),
    )
    return CarResponse.model_validate(car)


@router.put("/{car_id}/status", response_model=CarResponse)
async def set_car_status(
    car_id: UUID,
    payload: CarStatusUpdateRequest,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[CarService, Depends(get_car_service)],
) -> CarResponse:
    car = await service.set_status(
        CarStatusUpdateInput(organization_id=organization.id, car_id=car_id, status=payload.status),
    )
    return CarResponse.model_validate(car)


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_car(
    car_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[CarService, Depends(get_car_service)],
) -> Response:
    await service.delete(CarDeleteInput(organization_id=organization.id, car_id=car_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{car_id}/photos", response_model=list[CarPhotoResponse])
async def list_car_photos(
    car_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[CarService, Depends(get_car_service)],
) -> list[CarPhotoResponse]:
    photos = await service.list_photos(CarPhotosListInput(organization_id=organization.id, car_id=car_id))
    return [CarPhotoResponse.model_validate(photo) for photo in photos]


@router.put("/{car_id}/photos", response_model=list[CarPhotoResponse])
async def replace_car_photos(
    car_id: UUID,
    payload: list[CarPhotoRequest],
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[CarService, Depends(get_car_service)],
) -> list[CarPhotoResponse]:
    photos = await service.replace_photos(
        CarPhotosReplaceInput(
            organization_id=organization.id,
            car_id=car_id,
            photos=[CarPhotoInput(**photo.model_dump()) for photo in payload],
        ),
    )
    return [CarPhotoResponse.model_validate(photo) for photo in photos]


@router.post("/{car_id}/photos/upload", response_model=CarPhotoResponse, status_code=status.HTTP_201_CREATED)
async def upload_car_photo(
    car_id: UUID,
    request: Request,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[CarService, Depends(get_car_service)],
    filename: Annotated[str, Query(min_length=1, max_length=255)],
    position: Annotated[int, Query(ge=0)] = 0,
) -> CarPhotoResponse:
    photo = await service.upload_photo(
        CarPhotoUploadInput(
            organization_id=organization.id,
            car_id=car_id,
            filename=filename,
            content=await request.body(),
            position=position,
            content_type=request.headers.get("content-type"),
        ),
    )
    return CarPhotoResponse.model_validate(photo)


@router.get("/{car_id}/pricing-tiers", response_model=list[CarPricingTierResponse])
async def list_car_pricing_tiers(
    car_id: UUID,
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[CarService, Depends(get_car_service)],
) -> list[CarPricingTierResponse]:
    tiers = await service.list_pricing_tiers(CarPricingTiersListInput(organization_id=organization.id, car_id=car_id))
    return [CarPricingTierResponse.model_validate(tier) for tier in tiers]


@router.put("/{car_id}/pricing-tiers", response_model=list[CarPricingTierResponse])
async def replace_car_pricing_tiers(
    car_id: UUID,
    payload: list[CarPricingTierRequest],
    organization: Annotated[OrganizationDTO, Depends(get_current_organization)],
    service: Annotated[CarService, Depends(get_car_service)],
) -> list[CarPricingTierResponse]:
    tiers = await service.replace_pricing_tiers(
        CarPricingTiersReplaceInput(
            organization_id=organization.id,
            car_id=car_id,
            pricing_tiers=[CarPricingTierInput(**tier.model_dump()) for tier in payload],
        ),
    )
    return [CarPricingTierResponse.model_validate(tier) for tier in tiers]
