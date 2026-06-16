from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    id: UUID
    request_id: UUID
    user_id: UUID
    content: str
    created_at: datetime
    full_name: str | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def populate_user_info(cls, data):
        user = getattr(data, "user", None)
        if user is not None:
            try:
                # Set dynamic attribute so it maps to full_name field
                if hasattr(data, "__dict__"):
                    data.full_name = user.full_name or user.email
                else:
                    # For dict-like object
                    data["full_name"] = user.full_name or user.email
            except AttributeError:
                pass
        return data
