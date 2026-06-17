import json
from uuid import UUID

import httpx

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import r

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.request import RequestResponse, StatusUpdate
from app.schemas.resource import ResourceCreate, ResourceResponse, ResourceUpdate
from app.schemas.stats import AdminStatsResponse
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    return await admin_service.get_admin_stats(db)


@router.get("/requests", response_model=list[RequestResponse])
async def list_requests(
    status: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await admin_service.list_all_requests(
        db,
        status_filter=status,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )


@router.get("/requests/export")
async def export_requests(
    status: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    csv_content = await admin_service.export_requests_csv(
        db,
        status_filter=status,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=service_requests.csv"},
    )


@router.get("/requests/{request_id}", response_model=RequestResponse)
async def get_request(request_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    return await admin_service.get_request_by_id(db, request_id)


@router.patch("/requests/{request_id}/status", response_model=RequestResponse)
async def update_request_status(request_id: UUID, body: StatusUpdate, db: AsyncSession = Depends(get_db), request: Request = None, current_user: User = Depends(require_admin)):
    result = await admin_service.update_request_status(db, request_id, body.status, current_user.id, body.admin_note)
    try:
        r.delete(f"request:{request_id}")
    except Exception:
        pass
    try:
        from sqlalchemy import select
        from app.models.user import User
        user_res = await db.execute(select(User).where(User.id == result.user_id))
        user_obj = user_res.scalar_one_or_none()
        user_name = (user_obj.full_name or user_obj.email) if user_obj else "Unknown"
        user_email = user_obj.email if user_obj else "unknown"

        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:5678/webhook/48c0cd3b-20d8-43c2-a4dc-e6b5dfd208f9",
                    json={
                        "event": "status_changed",
                        "request_id": str(request_id),
                        "status": body.status,
                        "admin_note": body.admin_note,
                        "user_id": str(result.user_id),
                        "user_name": user_name,
                        "user_email": user_email,
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
            await pool.enqueue_job("send_notification", str(result.user_id), status_messages[body.status], str(request_id))
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
    resource = await admin_service.create_resource(
        db, body.name, body.type, body.description, body.capacity, body.location, body.image_url
    )
    r.delete("resources:all")
    return resource


@router.patch("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(resource_id: UUID, body: ResourceUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    resource = await admin_service.update_resource(
        db, resource_id, body.name, body.description, body.is_active, body.capacity, body.location, body.image_url
    )
    r.delete("resources:all")
    return resource


@router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    await admin_service.delete_resource(db, resource_id)
    r.delete("resources:all")
    return {"message": "Resource deleted successfully"}




@router.get("/stats/export")
async def export_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    csv_content = await admin_service.export_stats_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=admin_stats.csv"},
    )
