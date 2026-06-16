from datetime import date, datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.resource import Resource
from app.models.request import ServiceRequest
from app.schemas.resource import ResourceResponse

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("", response_model=list[ResourceResponse])
async def list_resources(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Resource).where(Resource.is_active == True).order_by(Resource.created_at.desc()))
    return list(result.scalars().all())


class BookedSlot(BaseModel):
    start_time: datetime
    end_time: datetime


@router.get("/{resource_id}/availability", response_model=list[BookedSlot])
async def get_resource_availability(
    resource_id: UUID,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format. Defaults to today."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all booked time slots (pending or approved) for a resource on a given date."""
    resource = await db.scalar(select(Resource).where(Resource.id == resource_id))
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    if date:
        try:
            day = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date format, use YYYY-MM-DD")
    else:
        day = datetime.now(timezone.utc).date()

    day_start = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=timezone.utc)
    day_end   = day_start + timedelta(days=1)

    result = await db.execute(
        select(ServiceRequest).where(
            and_(
                ServiceRequest.resource_id == resource_id,
                ServiceRequest.status.in_(["pending", "approved"]),
                ServiceRequest.start_time < day_end,
                ServiceRequest.end_time > day_start,
            )
        )
    )
    rows = result.scalars().all()
    return [BookedSlot(start_time=r.start_time, end_time=r.end_time) for r in rows if r.start_time and r.end_time]
