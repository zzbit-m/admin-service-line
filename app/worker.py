import uuid
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from arq.connections import RedisSettings

from app.core.config import settings


async def send_notification(ctx, user_id: str, message: str, request_id: str = None):
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with async_session() as db:
            # Import all models to register them in SQLAlchemy registry
            from app.models.user import User
            from app.models.resource import Resource
            from app.models.comment import RequestComment
            from app.models.attachment import Attachment
            from app.models.request import ServiceRequest

            # 1. Fetch user
            result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            user = result.scalar_one_or_none()
            if user is None or user.line_user_id is None:
                print(f"[send_notification] user {user_id}: no line_user_id, skipping")
                return

            # 2. Fetch request details if request_id is supplied
            request_obj = None
            if request_id:
                try:
                    req_result = await db.execute(
                        select(ServiceRequest).where(ServiceRequest.id == uuid.UUID(request_id))
                    )
                    request_obj = req_result.scalar_one_or_none()
                except Exception as ex:
                    print(f"[send_notification] error fetching request {request_id}: {ex}")

            # 3. Determine theme colors and text content for Flex Message
            theme_color = "#06C755"
            banner_text = "Service Notification"
            
            clean_msg = message
            for emoji in ["✅", "❌", "🚫", "💬", "🛑", "🔕", "📢", "⚡", "🔮"]:
                clean_msg = clean_msg.replace(emoji, "").strip()

            lower_msg = message.lower()
            if "approved" in lower_msg:
                theme_color = "#06C755"
                banner_text = "Request Approved"
            elif "rejected" in lower_msg:
                theme_color = "#EF4444"
                banner_text = "Request Rejected"
            elif "cancelled" in lower_msg:
                theme_color = "#78716C"
                banner_text = "Request Cancelled"
            elif "comment" in lower_msg:
                theme_color = "#3B82F6"
                banner_text = "New Comment"

            type_labels = {
                "room_booking": "🏢 Room",
                "vehicle_booking": "🚗 Vehicle",
                "maintenance": "🔧 Maintenance",
                "other": "📋 Other"
            }

            # 4. Construct Flex Message Bubble
            grid_items = []
            if request_obj:
                grid_items.append({
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "Title", "color": "#78716c", "size": "sm", "flex": 2},
                        {"type": "text", "text": request_obj.title or "—", "color": "#1c1917", "size": "sm", "weight": "bold", "wrap": True, "flex": 5}
                    ]
                })
                
                req_type = type_labels.get(request_obj.request_type, request_obj.request_type or "—")
                grid_items.append({
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "Type", "color": "#78716c", "size": "sm", "flex": 2},
                        {"type": "text", "text": req_type, "color": "#1c1917", "size": "sm", "wrap": True, "flex": 5}
                    ]
                })

                grid_items.append({
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "Status", "color": "#78716c", "size": "sm", "flex": 2},
                        {"type": "text", "text": request_obj.status.capitalize(), "color": "#1c1917", "size": "sm", "wrap": True, "flex": 5}
                    ]
                })

                if "comment" in lower_msg:
                    grid_items.append({
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "Comment", "color": "#78716c", "size": "sm", "flex": 2},
                            {"type": "text", "text": clean_msg, "color": "#1c1917", "size": "sm", "wrap": True, "style": "italic", "flex": 5}
                        ]
                    })
                elif request_obj.admin_note:
                    grid_items.append({
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "Note", "color": "#78716c", "size": "sm", "flex": 2},
                            {"type": "text", "text": request_obj.admin_note, "color": "#1c1917", "size": "sm", "wrap": True, "flex": 5}
                        ]
                    })
            else:
                grid_items.append({
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "Message", "color": "#78716c", "size": "sm", "flex": 2},
                        {"type": "text", "text": clean_msg, "color": "#1c1917", "size": "sm", "wrap": True, "flex": 5}
                    ]
                })

            liff_url = f"https://liff.line.me/{settings.LINE_LIFF_ID}"
            
            contents = {
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": theme_color,
                    "paddingAll": "16px",
                    "contents": [
                        {
                            "type": "text",
                            "text": "⚡ Service Portal",
                            "color": "#ffffff",
                            "weight": "bold",
                            "size": "sm"
                        }
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "paddingAll": "20px",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": banner_text,
                            "weight": "bold",
                            "size": "xl",
                            "color": "#1c1917"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "margin": "lg",
                            "contents": grid_items
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "paddingAll": "16px",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "Open Portal",
                                "uri": liff_url
                            },
                            "style": "primary",
                            "color": theme_color
                        }
                    ]
                }
            }

            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    "https://api.line.me/v2/bot/message/push",
                    headers={
                        "Authorization": f"Bearer {settings.LINE_MESSAGING_ACCESS_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "to": user.line_user_id,
                        "messages": [
                            {
                                "type": "flex",
                                "altText": f"📢 {banner_text}",
                                "contents": contents
                            }
                        ],
                    },
                )
                if resp.is_success:
                    print(f"[send_notification] pushed Flex Message to {user.line_user_id}: OK")
                else:
                    print(f"[send_notification] pushed Flex Message to {user.line_user_id}: FAILED {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[send_notification] error: {e}")
    finally:
        await engine.dispose()


class WorkerSettings:
    redis_settings = RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT, database=0)
    functions = [send_notification]
