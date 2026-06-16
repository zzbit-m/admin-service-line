from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comment import RequestComment
from app.models.request import ServiceRequest


async def create_comment(
    db: AsyncSession,
    request_id: UUID,
    user_id: UUID,
    user_role: str,
    content: str,
) -> RequestComment:
    # 1. Fetch request to verify existence and check authorization
    req_result = await db.execute(select(ServiceRequest).where(ServiceRequest.id == request_id))
    sr = req_result.scalar_one_or_none()
    if sr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    # 2. Authorization check: must be admin or the request owner
    if user_role != "admin" and sr.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to comment on this request",
        )

    # 3. Create comment
    comment = RequestComment(
        request_id=request_id,
        user_id=user_id,
        content=content.strip(),
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def get_comments(
    db: AsyncSession,
    request_id: UUID,
    user_id: UUID,
    user_role: str,
) -> list[RequestComment]:
    # 1. Fetch request to verify existence and check authorization
    req_result = await db.execute(select(ServiceRequest).where(ServiceRequest.id == request_id))
    sr = req_result.scalar_one_or_none()
    if sr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    # 2. Authorization check: must be admin or the request owner
    if user_role != "admin" and sr.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view comments for this request",
        )

    # 3. Fetch comments sorted chronologically (oldest first)
    result = await db.execute(
        select(RequestComment)
        .where(RequestComment.request_id == request_id)
        .order_by(RequestComment.created_at.asc())
    )
    return list(result.scalars().all())
