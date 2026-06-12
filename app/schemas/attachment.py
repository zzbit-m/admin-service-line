from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: UUID
    request_id: UUID
    file_url: str
    filename: str
    uploaded_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
