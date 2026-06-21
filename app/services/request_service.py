from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.request import ServiceRequest
from app.services.booking_conflict import assert_no_booking_conflict


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
        await assert_no_booking_conflict(db, resource_id, start_time, end_time)

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
        .options(selectinload(ServiceRequest.user))
        .where(ServiceRequest.user_id == user_id, ServiceRequest.is_archived == False)
        .order_by(ServiceRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_user_request_by_id(db: AsyncSession, user_id: UUID, request_id: UUID) -> ServiceRequest:
    result = await db.execute(
        select(ServiceRequest)
        .options(selectinload(ServiceRequest.user))
        .where(ServiceRequest.id == request_id, ServiceRequest.user_id == user_id)
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


async def archive_completed_requests(db: AsyncSession, user_id: UUID) -> int:
    from sqlalchemy import update
    stmt = (
        update(ServiceRequest)
        .where(
            ServiceRequest.user_id == user_id,
            ServiceRequest.status.in_(["approved", "rejected", "cancelled"]),
            ServiceRequest.is_archived == False
        )
        .values(is_archived=True)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount
