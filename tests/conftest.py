import os
import socket

os.environ.setdefault("SECRET_KEY", "pytest-secret-key-not-changeme-32b")
os.environ.setdefault("LINE_CHANNEL_ID", "2010375597")
os.environ.setdefault("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/test-uuid")

import uuid
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_local
from app.models.request import ServiceRequest
from app.models.user import User


def _postgres_reachable() -> bool:
    try:
        with socket.create_connection(("localhost", 5432), timeout=2):
            return True
    except OSError:
        return False


@pytest.fixture
def require_db():
    if not _postgres_reachable():
        pytest.skip("PostgreSQL is not available on localhost:5432")


@pytest.fixture
def fake_redis(monkeypatch):
    import fakeredis

    client = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.core.cache.r", client)
    return client


@pytest_asyncio.fixture
async def client(fake_redis, monkeypatch):
    mock_pool = AsyncMock()
    mock_pool.close = AsyncMock()
    monkeypatch.setattr("app.main.create_arq_pool", AsyncMock(return_value=mock_pool))

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def reset_db_pool_after_test():
    yield
    from app.db.session import engine

    await engine.dispose()


@pytest_asyncio.fixture
async def two_users_with_request(require_db):
    user_a = User(
        email=f"user_a_{uuid.uuid4().hex[:8]}@test.local",
        hashed_password=hash_password("password-a"),
        full_name="User A",
    )
    user_b = User(
        email=f"user_b_{uuid.uuid4().hex[:8]}@test.local",
        hashed_password=hash_password("password-b"),
        full_name="User B",
    )

    async with async_session_local() as db:
        db.add(user_a)
        db.add(user_b)
        await db.flush()

        sr = ServiceRequest(
            user_id=user_a.id,
            title="Cache IDOR test request",
            description="test",
        )
        db.add(sr)
        await db.commit()
        await db.refresh(user_a)
        await db.refresh(user_b)
        await db.refresh(sr)

        token_a = create_access_token({"sub": str(user_a.id)})
        token_b = create_access_token({"sub": str(user_b.id)})

        fixture_data = {
            "user_a": user_a,
            "user_b": user_b,
            "request": sr,
            "token_a": token_a,
            "token_b": token_b,
        }

    yield fixture_data

    async with async_session_local() as cleanup:
        for obj in (fixture_data["request"], fixture_data["user_a"], fixture_data["user_b"]):
            row = await cleanup.get(type(obj), obj.id)
            if row:
                await cleanup.delete(row)
        await cleanup.commit()
