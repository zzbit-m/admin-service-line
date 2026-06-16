from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request import ServiceRequest


async def create_request(
    db: AsyncSession,
    user_id: UUID,
    title: str,
    description: str | None,
    resource_id: UUID | None,
    request_type: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> ServiceRequest:
    if resource_id and start_time and end_time:
        conflict = await db.execute(
            select(ServiceRequest).where(
                ServiceRequest.resource_id == resource_id,
                ServiceRequest.status.in_(["pending", "approved"]),
                ServiceRequest.start_time < end_time,
                ServiceRequest.end_time > start_time,
            )
        )
        if conflict.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resource is not available for the requested time slot",
            )

    sr = ServiceRequest(
        user_id=user_id,
        title=title,
        description=description,
        request_type=request_type,
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
    )
    db.add(sr)
    await db.commit()
    await db.refresh(sr)
    return sr


async def get_user_requests(db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20) -> list[ServiceRequest]:
    result = await db.execute(
        select(ServiceRequest)
        .where(ServiceRequest.user_id == user_id)
        .order_by(ServiceRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_user_request_by_id(db: AsyncSession, user_id: UUID, request_id: UUID) -> ServiceRequest:
    result = await db.execute(
        select(ServiceRequest).where(ServiceRequest.id == request_id, ServiceRequest.user_id == user_id)
    )
    sr = result.scalar_one_or_none()
    if sr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )
    return sr


async def cancel_request(db: AsyncSession, user_id: UUID, request_id: UUID) -> ServiceRequest:
    result = await db.execute(
        select(ServiceRequest).where(ServiceRequest.id == request_id, ServiceRequest.user_id == user_id)
    )
    sr = result.scalar_one_or_none()
    if sr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )
    if sr.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be cancelled",
        )
    sr.status = "cancelled"
    await db.commit()
    await db.refresh(sr)
    return sr
