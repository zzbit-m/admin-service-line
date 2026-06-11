from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ResourceCreate(BaseModel):
    name: str
    type: Literal["room", "vehicle"]
    description: str | None = None


class ResourceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ResourceResponse(BaseModel):
    id: UUID
    name: str
    type: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
