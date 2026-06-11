from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request import ServiceRequest
from app.models.resource import Resource

VALID_TRANSITIONS = {
    "pending": {"approved", "rejected"},
    "approved": {"cancelled"},
    "rejected": set(),
    "cancelled": set(),
}


async def list_all_requests(db: AsyncSession, status_filter: str | None = None, skip: int = 0, limit: int = 20) -> list[ServiceRequest]:
    query = select(ServiceRequest).order_by(ServiceRequest.created_at.desc())
    if status_filter:
        query = query.where(ServiceRequest.status == status_filter)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


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
