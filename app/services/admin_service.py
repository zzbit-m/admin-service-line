from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.request import ServiceRequest
from app.models.resource import Resource

VALID_TRANSITIONS = {
    "pending": {"approved", "rejected"},
    "approved": {"cancelled"},
    "rejected": set(),
    "cancelled": set(),
}


async def list_all_requests(db: AsyncSession, status_filter: str | None = None, skip: int = 0, limit: int = 20) -> list[ServiceRequest]:
    query = select(ServiceRequest).options(selectinload(ServiceRequest.user)).order_by(ServiceRequest.created_at.desc())
    if status_filter:
        query = query.where(ServiceRequest.status == status_filter)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_request_by_id(db: AsyncSession, request_id: UUID) -> ServiceRequest:
    result = await db.execute(select(ServiceRequest).options(selectinload(ServiceRequest.user)).where(ServiceRequest.id == request_id))
    sr = result.scalar_one_or_none()
    if sr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return sr


async def update_request_status(db: AsyncSession, request_id: UUID, new_status: str, admin_note: str | None = None) -> ServiceRequest:
    result = await db.execute(select(ServiceRequest).where(ServiceRequest.id == request_id))
    sr = result.scalar_one_or_none()
    if sr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    allowed = VALID_TRANSITIONS.get(sr.status)
    if allowed is None or new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{sr.status}' to '{new_status}'",
        )

    sr.status = new_status
    if admin_note is not None:
        sr.admin_note = admin_note
    await db.commit()
    await db.refresh(sr)
    return sr


async def list_resources(db: AsyncSession) -> list[Resource]:
    result = await db.execute(select(Resource).order_by(Resource.created_at.desc()))
    return list(result.scalars().all())


async def create_resource(db: AsyncSession, name: str, type: str, description: str | None = None) -> Resource:
    resource = Resource(name=name, type=type, description=description)
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource


async def update_resource(db: AsyncSession, resource_id: UUID, name: str | None, description: str | None, is_active: bool | None) -> Resource:
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    if name is not None:
        resource.name = name
    if description is not None:
        resource.description = description
    if is_active is not None:
        resource.is_active = is_active
    await db.commit()
    await db.refresh(resource)
    return resource


async def get_admin_stats(db: AsyncSession) -> dict:
    from sqlalchemy import func, literal_column

    # 1. Total requests by status
    status_res = await db.execute(
        select(ServiceRequest.status, func.count(ServiceRequest.id)).group_by(ServiceRequest.status)
    )
    status_map = {row[0]: row[1] for row in status_res.all()}

    # 2. Request type distribution
    type_res = await db.execute(
        select(ServiceRequest.request_type, func.count(ServiceRequest.id)).group_by(ServiceRequest.request_type)
    )
    type_map = {row[0] or "other": row[1] for row in type_res.all()}

    # 3. Monthly reports (last 6 months)
    month_trunc = func.date_trunc(literal_column("'month'"), ServiceRequest.created_at)
    monthly_res = await db.execute(
        select(
            month_trunc.label('month_date'),
            func.count(ServiceRequest.id).label('total'),
            func.count(ServiceRequest.id).filter(ServiceRequest.status == 'approved').label('approved')
        )
        .group_by(month_trunc)
        .order_by(month_trunc)
    )
    monthly_list = [
        {
            "month": row.month_date.strftime('%b %Y') if row.month_date else "Unknown",
            "total": row.total,
            "approved": row.approved
        }
        for row in monthly_res.all()
    ][-6:]

    # 4. Weekly reports (last 4 weeks)
    week_trunc = func.date_trunc(literal_column("'week'"), ServiceRequest.created_at)
    weekly_res = await db.execute(
        select(
            week_trunc.label('week_date'),
            func.count(ServiceRequest.id).label('total')
        )
        .group_by(week_trunc)
        .order_by(week_trunc)
    )
    weekly_list = []
    for row in weekly_res.all():
        if row.week_date:
            isocal = row.week_date.isocalendar()
            week_str = f"{isocal[0]}-W{isocal[1]:02d}"
        else:
            week_str = "Unknown"
        weekly_list.append({
            "week": week_str,
            "total": row.total
        })
    weekly_list = weekly_list[-4:]

    return {
        "total_requests": {
            "pending": status_map.get("pending", 0),
            "approved": status_map.get("approved", 0),
            "rejected": status_map.get("rejected", 0),
            "cancelled": status_map.get("cancelled", 0),
        },
        "type_distribution": type_map,
        "monthly_reports": monthly_list,
        "weekly_reports": weekly_list,
    }


