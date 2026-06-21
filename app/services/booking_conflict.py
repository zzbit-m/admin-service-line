from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request import ServiceRequest
from app.models.resource import Resource


async def lock_resource_for_booking(db: AsyncSession, resource_id: UUID) -> None:
    result = await db.execute(
        select(Resource.id).where(Resource.id == resource_id).with_for_update()
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )


async def assert_no_booking_conflict(
    db: AsyncSession,
    resource_id: UUID,
    start_time: datetime,
    end_time: datetime,
    exclude_request_id: UUID | None = None,
    blocking_statuses: tuple[str, ...] = ("pending", "approved"),
) -> None:
    await lock_resource_for_booking(db, resource_id)

    query = select(ServiceRequest.id).where(
        ServiceRequest.resource_id == resource_id,
        ServiceRequest.status.in_(blocking_statuses),
        ServiceRequest.start_time < end_time,
        ServiceRequest.end_time > start_time,
    )
    if exclude_request_id is not None:
        query = query.where(ServiceRequest.id != exclude_request_id)

    conflict = await db.execute(query.limit(1))
    if conflict.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resource is not available for the requested time slot",
        )
