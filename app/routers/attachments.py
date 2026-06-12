from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.attachment import AttachmentResponse
from app.services import attachment_service

router = APIRouter(prefix="/requests", tags=["attachments"])


@router.post("/{request_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    request_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await attachment_service.upload_attachment(db, current_user, request_id, file)


@router.get("/{request_id}/attachments", response_model=list[AttachmentResponse])
async def list_attachments(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await attachment_service.list_attachments(db, current_user.id, request_id)
