from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, model_validator


class RequestCreate(BaseModel):
    resource_id: UUID | None = None
    title: str
    description: str | None = None
    request_type: str | None = None
    priority: Literal["low", "normal", "urgent"] = "normal"
    start_time: datetime | None = None
    end_time: datetime | None = None

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValueError("start_time must be before end_time")
        return self


class StatusUpdate(BaseModel):
    status: Literal["pending", "approved", "rejected", "cancelled"]
    admin_note: str | None = None


class ConflictDetail(BaseModel):
    id: UUID
    title: str
    full_name: str | None = None
    start_time: datetime
    end_time: datetime

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
    conflicts: list[ConflictDetail] = []

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
