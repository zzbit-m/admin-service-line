from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class RequestCreate(BaseModel):
    resource_id: UUID | None = None
    title: str
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class StatusUpdate(BaseModel):
    status: Literal["pending", "approved", "rejected", "cancelled"]
    admin_note: str | None = None


class RequestResponse(BaseModel):
    id: UUID
    user_id: UUID
    resource_id: UUID | None
    title: str
    description: str | None
    status: str
    admin_note: str | None
    start_time: datetime | None
    end_time: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
