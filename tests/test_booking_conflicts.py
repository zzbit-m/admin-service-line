from datetime import datetime, timedelta, timezone
import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_local
from app.models.request import ServiceRequest
from app.models.resource import Resource
from app.models.user import User
from app.schemas.request import RequestCreate


@pytest_asyncio.fixture
async def booking_fixture(require_db, fake_redis):
    from app.main import app

    admin = User(
        email=f"admin_{uuid.uuid4().hex[:8]}@test.local",
        hashed_password=hash_password("admin-pass"),
        role="admin",
        full_name="Admin",
    )
    user = User(
        email=f"booker_{uuid.uuid4().hex[:8]}@test.local",
        hashed_password=hash_password("user-pass"),
        full_name="Booker",
    )
    resource = Resource(name="Test Room", type="room")

    async with async_session_local() as db:
        db.add(admin)
        db.add(user)
        db.add(resource)
        await db.commit()
        await db.refresh(admin)
        await db.refresh(user)
        await db.refresh(resource)

        start = datetime.now(timezone.utc) + timedelta(days=1)
        end = start + timedelta(hours=1)

        req_a = ServiceRequest(
            user_id=user.id,
            resource_id=resource.id,
            title="Booking A",
            start_time=start,
            end_time=end,
            status="pending",
        )
        req_b = ServiceRequest(
            user_id=user.id,
            resource_id=resource.id,
            title="Booking B",
            start_time=start,
            end_time=end,
            status="pending",
        )
        db.add(req_a)
        await db.commit()
        await db.refresh(req_a)

        db.add(req_b)
        await db.commit()
        await db.refresh(req_b)

        admin_token = create_access_token({"sub": str(admin.id)})

        data = {
            "admin": admin,
            "user": user,
            "resource": resource,
            "req_a": req_a,
            "req_b": req_b,
            "admin_token": admin_token,
            "app": app,
        }

    yield data

    async with async_session_local() as cleanup:
        for obj in (data["req_b"], data["req_a"], data["resource"], data["user"], data["admin"]):
            row = await cleanup.get(type(obj), obj.id)
            if row:
                await cleanup.delete(row)
        await cleanup.commit()


@pytest.mark.asyncio
async def test_approve_second_overlapping_request_returns_409(booking_fixture):
    app = booking_fixture["app"]
    req_a = booking_fixture["req_a"]
    req_b = booking_fixture["req_b"]
    admin_token = booking_fixture["admin_token"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.patch(
            f"/admin/requests/{req_a.id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "approved"},
        )
        assert first.status_code == 200

        second = await client.patch(
            f"/admin/requests/{req_b.id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "approved"},
        )
        assert second.status_code == 409


def test_request_create_invalid_time_range():
    start = datetime.now(timezone.utc) + timedelta(days=2)
    end = start - timedelta(hours=1)
    with pytest.raises(ValidationError):
        RequestCreate(
            title="Bad times",
            start_time=start,
            end_time=end,
        )


@pytest.mark.asyncio
async def test_create_request_rejects_invalid_time_range(require_db, client, fake_redis):
    user = User(
        email=f"timerange_{uuid.uuid4().hex[:8]}@test.local",
        hashed_password=hash_password("password"),
    )
    async with async_session_local() as db:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        token = create_access_token({"sub": str(user.id)})
        user_id = user.id

    start = datetime.now(timezone.utc) + timedelta(days=2)
    end = start - timedelta(hours=1)

    res = await client.post(
        "/requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Bad times",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )
    assert res.status_code == 422

    async with async_session_local() as db:
        row = await db.get(User, user_id)
        if row:
            await db.delete(row)
            await db.commit()


@pytest.mark.asyncio
async def test_concurrent_approve_only_one_succeeds(booking_fixture):
    app = booking_fixture["app"]
    req_a = booking_fixture["req_a"]
    req_b = booking_fixture["req_b"]
    admin_token = booking_fixture["admin_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    transport = ASGITransport(app=app)

    async def approve(request_id):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.patch(
                f"/admin/requests/{request_id}/status",
                headers=headers,
                json={"status": "approved"},
            )

    results = await asyncio.gather(
        approve(req_a.id),
        approve(req_b.id),
        return_exceptions=True,
    )
    status_codes = [r.status_code for r in results if not isinstance(r, Exception)]
    assert 200 in status_codes
    assert 409 in status_codes
