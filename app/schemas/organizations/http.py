from pydantic import BaseModel, Field
from schemas.base.common import BaseEntityResponse

__all__ = ["OrganizationCreateRequest", "OrganizationResponse", "OrganizationUpdateRequest"]


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class OrganizationUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class OrganizationResponse(BaseEntityResponse):
    name: str
