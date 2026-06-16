import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from arq.connections import RedisSettings

from app.core.config import settings


async def send_notification(ctx, user_id: str, message: str):
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with async_session() as db:
            from app.models.user import User

            result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            user = result.scalar_one_or_none()
            if user is None or user.line_user_id is None:
                print(f"[send_notification] user {user_id}: no line_user_id, skipping")
                return
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    "https://api.line.me/v2/bot/message/push",
                    headers={
                        "Authorization": f"Bearer {settings.LINE_MESSAGING_ACCESS_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "to": user.line_user_id,
                        "messages": [{"type": "text", "text": message}],
                    },
                )
                if resp.is_success:
                    print(f"[send_notification] pushed to {user.line_user_id}: OK")
                else:
                    print(f"[send_notification] pushed to {user.line_user_id}: FAILED {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[send_notification] error: {e}")
    finally:
        await engine.dispose()


class WorkerSettings:
    redis_settings = RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT, database=0)
    functions = [send_notification]
