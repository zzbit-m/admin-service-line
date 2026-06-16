from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class RequestCreate(BaseModel):
    resource_id: UUID | None = None
    title: str
    description: str | None = None
    request_type: str | None = None
    priority: Literal["low", "normal", "urgent"] = "normal"
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
    request_type: str | None
    priority: str
    status: str
    admin_note: str | None
    is_archived: bool
    full_name: str | None = None
    start_time: datetime | None
    end_time: datetime | None
    resolved_by: UUID | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    from pydantic import model_validator

    @model_validator(mode="before")
    @classmethod
    def populate_user_info(cls, data):
        user = getattr(data, "user", None)
        if user is not None:
            try:
                data.full_name = user.full_name or user.email
            except AttributeError:
                pass
        return data
