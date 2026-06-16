import json
from uuid import UUID

import httpx

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import r
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.request import RequestCreate, RequestResponse
from app.services import request_service

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(body: RequestCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    sr = await request_service.create_request(
        db, current_user.id, body.title, body.description, body.resource_id, body.request_type, body.start_time, body.end_time
    )
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:5678/webhook/48c0cd3b-20d8-43c2-a4dc-e6b5dfd208f9",
                json={
                    "event": "request_created",
                    "request_id": str(sr.id),
                    "user_id": str(sr.user_id),
                    "user_name": current_user.full_name or current_user.email,
                    "user_email": current_user.email,
                    "title": sr.title,
                    "resource_id": str(sr.resource_id) if sr.resource_id else None,
                },
                timeout=3.0,
            )
    except Exception:
        pass
    return sr


@router.get("/me", response_model=list[RequestResponse])
async def list_my_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await request_service.get_user_requests(db, current_user.id, skip, limit)


@router.post("/archive", status_code=status.HTTP_200_OK)
async def archive_my_history(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = await request_service.archive_completed_requests(db, current_user.id)
    return {"message": "History cleared", "archived_count": count}


@router.patch("/{request_id}/cancel", response_model=RequestResponse)
async def cancel_request(request_id: UUID, db: AsyncSession = Depends(get_db), request: Request = None, current_user: User = Depends(get_current_user)):
    sr = await request_service.cancel_request(db, current_user.id, request_id)
    try:
        r.delete(f"request:{request_id}")
    except Exception:
        pass
    try:
        pool = request.app.state.arq_pool
        await pool.enqueue_job("send_notification", str(sr.user_id), "\U0001f6ab Your request has been cancelled.")
    except Exception:
        pass
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:5678/webhook/48c0cd3b-20d8-43c2-a4dc-e6b5dfd208f9",
                json={
                    "event": "request_cancelled",
                    "request_id": str(request_id),
                    "user_id": str(sr.user_id),
                    "user_name": current_user.full_name or current_user.email,
                    "user_email": current_user.email,
                },
                timeout=3.0,
            )
    except Exception:
        pass
    return sr


@router.get("/{request_id}", response_model=RequestResponse)
async def get_request(request_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    cache_key = f"request:{request_id}"
    try:
        cached = r.get(cache_key)
        if cached is not None:
            return RequestResponse(**json.loads(cached))
    except Exception:
        pass
    sr = await request_service.get_user_request_by_id(db, current_user.id, request_id)
    try:
        r.setex(cache_key, 30, json.dumps(RequestResponse.model_validate(sr).model_dump(mode="json")))
    except Exception:
        pass
    return sr
