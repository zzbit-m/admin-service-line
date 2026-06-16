import json
from uuid import UUID

import httpx

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import r

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
async def update_request_status(request_id: UUID, body: StatusUpdate, db: AsyncSession = Depends(get_db), request: Request = None, current_user: User = Depends(require_admin)):
    result = await admin_service.update_request_status(db, request_id, body.status, body.admin_note)
    try:
        r.delete(f"request:{request_id}")
    except Exception:
        pass
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:5678/webhook-test/48c0cd3b-20d8-43c2-a4dc-e6b5dfd208f9",
                json={
                    "request_id": str(request_id),
                    "status": body.status,
                    "admin_note": body.admin_note,
                }
            )
    except Exception:
        pass
    try:
        pool = request.app.state.arq_pool
        status_messages = {
            "approved": "\u2705 Your request has been approved.",
            "rejected": "\u274c Your request has been rejected.",
        }
        if body.status in status_messages:
            await pool.enqueue_job("send_notification", str(result.user_id), status_messages[body.status])
    except Exception:
        pass
    return result


@router.get("/resources", response_model=list[ResourceResponse])
async def list_resources(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    cache_key = "resources:all"
    cached = r.get(cache_key)
    if cached is not None:
        return [ResourceResponse(**item) for item in json.loads(cached)]

    resources = await admin_service.list_resources(db)
    data = [ResourceResponse.model_validate(res).model_dump(mode="json") for res in resources]
    r.setex(cache_key, 60, json.dumps(data))
    return data


@router.post("/resources", response_model=ResourceResponse, status_code=201)
async def create_resource(body: ResourceCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    resource = await admin_service.create_resource(db, body.name, body.type, body.description)
    r.delete("resources:all")
    return resource


@router.patch("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(resource_id: UUID, body: ResourceUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    resource = await admin_service.update_resource(db, resource_id, body.name, body.description, body.is_active)
    r.delete("resources:all")
    return resource
