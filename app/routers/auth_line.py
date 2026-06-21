import secrets
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import get_db

router = APIRouter()

LINE_VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify"
LINE_PROFILE_URL = "https://api.line.me/v2/profile"
LINE_CHANNEL_ID = settings.LINE_CHANNEL_ID


class LineAuthRequest(BaseModel):
    access_token: str


@router.post("/auth/line")
async def line_login(body: LineAuthRequest, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        verify_resp = await client.get(
            LINE_VERIFY_URL,
            params={"access_token": body.access_token}
        )

    if verify_resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid LINE access token")

    if str(verify_resp.json().get("client_id")) != str(LINE_CHANNEL_ID):
        raise HTTPException(status_code=401, detail="Token not issued for this app")

    async with httpx.AsyncClient() as client:
        profile_resp = await client.get(
            LINE_PROFILE_URL,
            headers={"Authorization": f"Bearer {body.access_token}"}
        )

    if profile_resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Failed to fetch LINE profile")

    profile = profile_resp.json()
    line_user_id = profile["userId"]

    result = await db.execute(
        text("SELECT id, email, role FROM users WHERE line_user_id = :lid"),
        {"lid": line_user_id}
    )
    user = result.fetchone()

    if not user:
        insert = await db.execute(
            text("""
                INSERT INTO users (id, email, full_name, hashed_password, role, line_user_id, is_active, created_at)
                VALUES (:id, :email, :name, :pw, 'user', :lid, true, :now)
                RETURNING id, email, role
            """),
            {
                "id": str(uuid.uuid4()),
                "email": f"line_{line_user_id}@line.local",
                "name": profile.get("displayName", ""),
                "pw": hash_password(secrets.token_hex(32)),
                "lid": line_user_id,
                "now": datetime.now(timezone.utc),
            }
        )
        await db.commit()
        user = insert.fetchone()

    token = create_access_token({"sub": str(user.id), "role": user.role})
    
    try:
        from app.routers.webhook import update_user_rich_menu
        await update_user_rich_menu(line_user_id, user.role == "admin")
    except Exception as e:
        print(f"Error updating rich menu on login: {e}")

    return {"access_token": token, "token_type": "bearer"}
