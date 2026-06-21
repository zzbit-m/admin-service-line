import asyncio
import logging

import httpx
from fastapi import BackgroundTasks

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _post_n8n(payload: dict) -> None:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.N8N_WEBHOOK_URL,
                json=payload,
                timeout=3.0,
            )
            if not resp.is_success:
                logger.warning(
                    "n8n webhook failed: status=%s body=%s",
                    resp.status_code,
                    resp.text[:500],
                )
    except Exception as ex:
        logger.warning("n8n webhook error: %s", ex)


def fire_n8n_event(payload: dict, background_tasks: BackgroundTasks | None = None) -> None:
    if background_tasks is not None:
        background_tasks.add_task(_post_n8n, payload)
    else:
        asyncio.create_task(_post_n8n(payload))
