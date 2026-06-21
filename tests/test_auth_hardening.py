import subprocess
import sys
import uuid

import bcrypt
import pytest

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_local
from app.models.user import User


@pytest.mark.asyncio
async def test_deactivated_user_returns_403(require_db, client):
    user = User(
        email=f"inactive_{uuid.uuid4().hex[:8]}@test.local",
        hashed_password=hash_password("password"),
        is_active=False,
    )
    async with async_session_local() as db:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        user_id = user.id
        token = create_access_token({"sub": str(user_id)})

    res = await client.get("/requests/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

    async with async_session_local() as db:
        row = await db.get(User, user_id)
        if row:
            await db.delete(row)
            await db.commit()


def test_line_user_password_is_bcrypt_hash():
    hashed = hash_password("not-used")
    assert hashed != "LINE_OAUTH"
    assert hashed.startswith("$2")
    assert bcrypt.checkpw(b"probe", hashed.encode("utf-8")) is False


def test_settings_fail_fast_on_default_secret_key():
    env = {
        **{k: v for k, v in __import__("os").environ.items()},
        "SECRET_KEY": "changeme",
        "LINE_CHANNEL_ID": "123",
        "LINE_MESSAGING_CHANNEL_SECRET": "secret",
        "N8N_WEBHOOK_URL": "http://localhost:5678/webhook/x",
    }
    result = subprocess.run(
        [sys.executable, "-c", "import app.core.config"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
    )
    assert result.returncode != 0
    combined = (result.stderr or "") + (result.stdout or "")
    assert "SECRET_KEY" in combined
