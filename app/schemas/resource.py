from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ResourceCreate(BaseModel):
    name: str
    type: Literal["room", "vehicle", "equipment", "other"]
    description: str | None = None
    capacity: int | None = None
    location: str | None = None
    image_url: str | None = None


class ResourceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    capacity: int | None = None
    location: str | None = None
    image_url: str | None = None
    is_active: bool | None = None


class ResourceResponse(BaseModel):
    id: UUID
    name: str
    type: str
    description: str | None
    capacity: int | None = None
    location: str | None = None
    image_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
