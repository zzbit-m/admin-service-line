from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.models.attachment import Attachment
from app.models.request import ServiceRequest

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "application/pdf"}
MAX_SIZE = 5 * 1024 * 1024


async def upload_attachment(
    db: AsyncSession,
    current_user: "User",
    request_id: UUID,
    file: UploadFile,
) -> Attachment:
    result = await db.execute(select(ServiceRequest).where(ServiceRequest.id == request_id))
    sr = result.scalar_one_or_none()
    if sr is None or sr.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' is not allowed",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit",
        )

    # Pass pre-read bytes directly to avoid double-read (file stream already consumed)
    file_url = await storage.upload_file_bytes(file.filename, file.content_type, file_bytes, folder="attachments")

    attachment = Attachment(
        request_id=request_id,
        file_url=file_url,
        filename=file.filename or "unnamed",
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


async def list_attachments(db: AsyncSession, user_id: UUID, request_id: UUID) -> list[Attachment]:
    result = await db.execute(select(ServiceRequest).where(ServiceRequest.id == request_id))
    sr = result.scalar_one_or_none()
    if sr is None or sr.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    result = await db.execute(
        select(Attachment).where(Attachment.request_id == request_id).order_by(Attachment.created_at.desc())
    )
    return list(result.scalars().all())
