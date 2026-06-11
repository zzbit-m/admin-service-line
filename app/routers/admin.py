from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.request import RequestResponse, StatusUpdate
from app.schemas.resource import ResourceCreate, ResourceResponse, ResourceUpdate
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/requests", response_model=list[RequestResponse])
async def list_requests(
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await admin_service.list_all_requests(db, status, skip, limit)


@router.patch("/requests/{request_id}/status", response_model=RequestResponse)
async def update_request_status(request_id: UUID, body: StatusUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    return await admin_service.update_request_status(db, request_id, body.status, body.admin_note)


@router.get("/resources", response_model=list[ResourceResponse])
async def list_resources(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    return await admin_service.list_resources(db)


@router.post("/resources", response_model=ResourceResponse, status_code=201)
async def create_resource(body: ResourceCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    return await admin_service.create_resource(db, body.name, body.type, body.description)


@router.patch("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(resource_id: UUID, body: ResourceUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    return await admin_service.update_resource(db, resource_id, body.name, body.description, body.is_active)
