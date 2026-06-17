import hashlib
import hmac
import base64
import httpx
from fastapi import APIRouter, Request, HTTPException
from app.core.config import settings

router = APIRouter()

LIFF_URL = f"https://liff.line.me/{settings.LINE_LIFF_ID}"

async def send_reply(reply_token: str, messages: list):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.line.me/v2/bot/message/reply",
                headers={"Authorization": f"Bearer {settings.LINE_MESSAGING_ACCESS_TOKEN}"},
                json={"replyToken": reply_token, "messages": messages},
                timeout=5.0
            )
            # Safe print/logging of the response status
            print(f"LINE reply API status: {resp.status_code}")
    except Exception as e:
        print(f"Error calling LINE reply API: {e}")

async def get_line_profile(user_id: str) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.line.me/v2/bot/profile/{user_id}",
                headers={"Authorization": f"Bearer {settings.LINE_MESSAGING_ACCESS_TOKEN}"},
                timeout=3.0
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"Error fetching LINE bot profile for {user_id}: {e}")
    return {}

@router.post("/webhook/line")
async def line_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    hash = hmac.new(
        settings.LINE_MESSAGING_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    expected = base64.b64encode(hash).decode("utf-8")

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()

    for event in data.get("events", []):
        if event.get("type") == "message" and event["message"]["type"] == "text":
            reply_token = event["replyToken"]
            text = event["message"]["text"].strip().lower()

            if text in ["hi", "hello", "hey", "menu", "help", "start", "home", "book", "booking", "สวัสดี", "เมนู"]:
                # Check user role and name based on line_user_id
                line_user_id = event.get("source", {}).get("userId")
                is_admin = False
                user_name = "there"
                if line_user_id:
                    # Fetch real profile display name from LINE first
                    profile = await get_line_profile(line_user_id)
                    if profile and profile.get("displayName"):
                        user_name = profile["displayName"]
                        
                    try:
                        from sqlalchemy import select
                        from app.db.session import async_session_local
                        from app.models.user import User
                        async with async_session_local() as db:
                            res = await db.execute(select(User).where(User.line_user_id == line_user_id))
                            user = res.scalar_one_or_none()
                            if user:
                                # Save/sync the real display name to database if missing or has default 'line_...' email prefix as name
                                if not user.full_name or user.full_name.startswith("line_") or user.full_name == "":
                                    user.full_name = user_name
                                    await db.commit()
                                else:
                                    user_name = user.full_name
                                    
                                if user.role == "admin":
                                    is_admin = True
                    except Exception as e:
                        print(f"Error checking DB profile: {e}")

                # Build menu options
                contents_list = [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "backgroundColor": "#ECFDF5",
                        "paddingAll": "14px",
                        "cornerRadius": "lg",
                        "action": {
                            "type": "uri",
                            "label": "New Request",
                            "uri": f"{LIFF_URL}?page=new"
                        },
                        "alignItems": "center",
                        "contents": [
                            {
                                "type": "text",
                                "text": "📝",
                                "size": "xl",
                                "flex": 0
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "margin": "lg",
                                "flex": 1,
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "New Request",
                                        "weight": "bold",
                                        "size": "sm",
                                        "color": "#065F46"
                                    },
                                    {
                                        "type": "text",
                                        "text": "Book a room, vehicle, equipment, or other request",
                                        "size": "xxs",
                                        "color": "#059669",
                                        "wrap": True
                                    }
                                ]
                            },
                            {
                                "type": "text",
                                "text": ">",
                                "size": "lg",
                                "color": "#A7F3D0",
                                "flex": 0,
                                "align": "end"
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "backgroundColor": "#EFF6FF",
                        "paddingAll": "14px",
                        "cornerRadius": "lg",
                        "action": {
                            "type": "uri",
                            "label": "My Requests",
                            "uri": f"{LIFF_URL}?page=requests"
                        },
                        "alignItems": "center",
                        "contents": [
                            {
                                "type": "text",
                                "text": "📋",
                                "size": "xl",
                                "flex": 0
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "margin": "lg",
                                "flex": 1,
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "My Requests",
                                        "weight": "bold",
                                        "size": "sm",
                                        "color": "#1E40AF"
                                    },
                                    {
                                        "type": "text",
                                        "text": "View status and track your requests",
                                        "size": "xxs",
                                        "color": "#3B82F6",
                                        "wrap": True
                                    }
                                ]
                            },
                            {
                                "type": "text",
                                "text": ">",
                                "size": "lg",
                                "color": "#BFDBFE",
                                "flex": 0,
                                "align": "end"
                            }
                        ]
                    }
                ]

                if is_admin:
                    contents_list.append({
                        "type": "box",
                        "layout": "horizontal",
                        "backgroundColor": "#F0FDFA",
                        "paddingAll": "14px",
                        "cornerRadius": "lg",
                        "action": {
                            "type": "uri",
                            "label": "Admin Dashboard",
                            "uri": f"{LIFF_URL}?page=admin"
                        },
                        "alignItems": "center",
                        "contents": [
                            {
                                "type": "text",
                                "text": "⚡",
                                "size": "xl",
                                "flex": 0
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "margin": "lg",
                                "flex": 1,
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "Admin Dashboard",
                                        "weight": "bold",
                                        "size": "sm",
                                        "color": "#0F766E"
                                    },
                                    {
                                        "type": "text",
                                        "text": "Manage requests, resources, and reports",
                                        "size": "xxs",
                                        "color": "#0D9488",
                                        "wrap": True
                                    }
                                ]
                            },
                            {
                                "type": "text",
                                "text": ">",
                                "size": "lg",
                                "color": "#99F6E4",
                                "flex": 0,
                                "align": "end"
                            }
                        ]
                    })

                # Dynamic customization for admins vs users (green theme)
                start_color = "#06C755"
                end_color = "#04964A"
                title_text = "Admin Control Panel" if is_admin else "Service Portal"
                subtitle_text = "System Control & Approvals" if is_admin else "Booking & Request Management"
                sub_color = "#C8F5D8"
                greeting_text = f"Hello Admin {user_name}! What would you like to manage?" if is_admin else f"Hi {user_name}! What would you like to do?"
                footer_text = "Tip: You can type \"pending\" to review requests." if is_admin else "Tip: You can type \"hi\" anytime to see this again."

                if is_admin:
                    intro_text = (
                        f"Welcome to the Admin Service Portal, {user_name}! ⚡\n\n"
                        "This portal allows you to manage requests, review pending approvals, and view analytics reports. "
                        "Tap a button below to get started."
                    )
                else:
                    intro_text = (
                        f"Welcome to the Service Portal, {user_name}! 📝\n\n"
                        "You can book rooms/vehicles, submit maintenance tasks, and track request statuses. "
                        "Tap a button below to submit a new request."
                    )

                await send_reply(reply_token, [
                    {
                        "type": "text",
                        "text": intro_text
                    },
                    {
                        "type": "flex",
                        "altText": "Welcome to Service Portal! Tap to get started.",
                        "contents": {
                            "type": "bubble",
                            "size": "mega",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "background": {
                                    "type": "linearGradient",
                                    "angle": "135deg",
                                    "startColor": start_color,
                                    "endColor": end_color
                                },
                                "paddingAll": "24px",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": title_text,
                                        "weight": "bold",
                                        "color": "#ffffff",
                                        "size": "xl"
                                    },
                                    {
                                        "type": "text",
                                        "text": subtitle_text,
                                        "color": sub_color,
                                        "size": "xs",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "20px",
                                "spacing": "lg",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": greeting_text,
                                        "weight": "bold",
                                        "size": "sm",
                                        "color": "#1E293B",
                                        "wrap": True
                                    },
                                    {
                                        "type": "separator",
                                        "color": "#E2E8F0"
                                    },
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "spacing": "sm",
                                        "contents": contents_list
                                    }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "14px",
                                "backgroundColor": "#F8FAFC",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": footer_text,
                                        "size": "xxs",
                                        "color": "#94A3B8",
                                        "align": "center"
                                    }
                                ]
                            }
                        }
                    }
                ])
            elif text in ["status", "requests", "request", "history", "track", "my status", "my requests", "สถานะ"]:
                # Fetch recent requests for this user
                line_user_id = event.get("source", {}).get("userId")
                user = None
                requests = []
                if line_user_id:
                    try:
                        from sqlalchemy import select
                        from app.db.session import async_session_local
                        from app.models.user import User
                        from app.models.request import ServiceRequest
                        async with async_session_local() as db:
                            res = await db.execute(select(User).where(User.line_user_id == line_user_id))
                            user = res.scalar_one_or_none()
                            if user:
                                reqs_res = await db.execute(
                                    select(ServiceRequest)
                                    .where(ServiceRequest.user_id == user.id)
                                    .order_by(ServiceRequest.created_at.desc())
                                    .limit(5)
                                )
                                requests = reqs_res.scalars().all()
                    except Exception:
                        pass

                if not user:
                    # Not linked or doesn't exist
                    await send_reply(reply_token, [
                        {
                            "type": "text",
                            "text": "It looks like your LINE account is not linked to any user on our Service Portal yet.\n\nTap below to open the portal and sign in to link your account!",
                            "quickReply": {
                                "items": [
                                    {
                                        "type": "action",
                                        "action": {
                                            "type": "uri",
                                            "label": "Open Portal",
                                            "uri": LIFF_URL
                                        }
                                    }
                                ]
                            }
                        }
                    ])
                elif not requests:
                    # Linked, but no requests yet
                    await send_reply(reply_token, [
                        {
                            "type": "flex",
                            "altText": "No requests found",
                            "contents": {
                                "type": "bubble",
                                "body": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "My Requests",
                                            "weight": "bold",
                                            "size": "lg",
                                            "color": "#1E293B"
                                        },
                                        {
                                            "type": "text",
                                            "text": "You haven't submitted any requests yet.",
                                            "size": "sm",
                                            "color": "#64748B",
                                            "margin": "md",
                                            "wrap": True
                                        }
                                    ]
                                },
                                "footer": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {
                                            "type": "button",
                                            "action": {
                                                "type": "uri",
                                                "label": "Submit New Request",
                                                "uri": f"{LIFF_URL}?page=new"
                                            },
                                            "style": "primary",
                                            "color": "#06C755"
                                        }
                                    ]
                                }
                            }
                        }
                    ])
                else:
                    # Map request type to emojis and status to colors
                    type_emojis = {
                        "room_booking": "🏢",
                        "vehicle_booking": "🚗",
                        "maintenance": "🔧",
                        "other": "📋"
                    }
                    status_colors = {
                        "pending": "#f59e0b",
                        "approved": "#10b981",
                        "rejected": "#ef4444",
                        "cancelled": "#94a3b8"
                    }
                    status_bg_colors = {
                        "pending": "#fffbeb",
                        "approved": "#ecfdf5",
                        "rejected": "#fef2f2",
                        "cancelled": "#f1f5f9"
                    }

                    # Build request items list
                    request_items = []
                    for r in requests:
                        emoji = type_emojis.get(r.request_type, "📋")
                        status_color = status_colors.get(r.status, "#64748B")
                        status_bg = status_bg_colors.get(r.status, "#f8fafc")
                        status_text = r.status.upper()

                        request_items.append({
                            "type": "box",
                            "layout": "horizontal",
                            "paddingAll": "10px",
                            "backgroundColor": "#FFFFFF",
                            "borderColor": "#E2E8F0",
                            "borderWidth": "1px",
                            "cornerRadius": "md",
                            "alignItems": "center",
                            "action": {
                                "type": "uri",
                                "label": "View Detail",
                                "uri": f"{LIFF_URL}?page=detail&id={r.id}"
                            },
                            "contents": [
                                {
                                    "type": "text",
                                    "text": emoji,
                                    "size": "lg",
                                    "flex": 0
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "margin": "md",
                                    "flex": 1,
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": r.title,
                                            "weight": "bold",
                                            "size": "xs",
                                            "color": "#1E293B",
                                            "maxLines": 1,
                                            "wrap": False
                                        },
                                        {
                                            "type": "text",
                                            "text": r.created_at.strftime("%b %d, %Y") if r.created_at else "",
                                            "size": "xxs",
                                            "color": "#94A3B8"
                                        }
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "flex": 0,
                                    "backgroundColor": status_bg,
                                    "cornerRadius": "sm",
                                    "paddingStart": "6px",
                                    "paddingEnd": "6px",
                                    "paddingTop": "2px",
                                    "paddingBottom": "2px",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": status_text,
                                            "color": status_color,
                                            "size": "xxs",
                                            "weight": "bold",
                                            "align": "center"
                                        }
                                    ]
                                }
                            ]
                        })

                    # Construct final Flex bubble
                    flex_contents = {
                        "type": "bubble",
                        "size": "mega",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "background": {
                                "type": "linearGradient",
                                "angle": "135deg",
                                "startColor": "#3B82F6",
                                "endColor": "#1E40AF"
                            },
                            "paddingAll": "20px",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "My Recent Requests",
                                    "weight": "bold",
                                    "color": "#FFFFFF",
                                    "size": "md"
                                },
                                {
                                    "type": "text",
                                    "text": f"Showing last {len(requests)} requests",
                                    "color": "#BFDBFE",
                                    "size": "xxs",
                                    "margin": "xs"
                                }
                            ]
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "paddingAll": "16px",
                            "spacing": "sm",
                            "backgroundColor": "#F8FAFC",
                            "contents": request_items
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "paddingAll": "12px",
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "uri",
                                        "label": "View All in Portal",
                                        "uri": f"{LIFF_URL}?page=requests"
                                    },
                                    "style": "link",
                                    "height": "sm"
                                },
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "uri",
                                        "label": "＋ New Request",
                                        "uri": f"{LIFF_URL}?page=new"
                                    },
                                    "style": "primary",
                                    "color": "#06C755",
                                    "height": "sm"
                                }
                            ]
                        }
                    }

                    await send_reply(reply_token, [
                        {
                            "type": "flex",
                            "altText": "My Recent Requests",
                            "contents": flex_contents
                        }
                    ])

            elif text in ["pending", "admin", "review", "stat", "stats", "reports", "อนุมัติ"]:
                # Check user role and get pending counts
                line_user_id = event.get("source", {}).get("userId")
                user = None
                pending_count = 0
                pending_requests = []
                if line_user_id:
                    try:
                        from sqlalchemy import select, func
                        from sqlalchemy.orm import selectinload
                        from app.db.session import async_session_local
                        from app.models.user import User
                        from app.models.request import ServiceRequest
                        async with async_session_local() as db:
                            res = await db.execute(select(User).where(User.line_user_id == line_user_id))
                            user = res.scalar_one_or_none()
                            if user and user.role == "admin":
                                # get count of pending requests
                                count_res = await db.execute(
                                    select(func.count(ServiceRequest.id))
                                    .where(ServiceRequest.status == "pending")
                                )
                                pending_count = count_res.scalar() or 0

                                # get first 4 pending requests for carousel cards
                                if pending_count > 0:
                                    reqs_res = await db.execute(
                                        select(ServiceRequest)
                                        .options(selectinload(ServiceRequest.user))
                                        .where(ServiceRequest.status == "pending")
                                        .order_by(ServiceRequest.created_at.asc())
                                        .limit(4)
                                    )
                                    pending_requests = reqs_res.scalars().all()
                    except Exception as e:
                        print(f"Error loading pending requests: {e}")

                if not user or user.role != "admin":
                    # Non-admin trying to access admin dashboard info
                    await send_reply(reply_token, [
                        {
                            "type": "text",
                            "text": "Sorry, only administrators can access the review summary.\n\nType 'hi' or 'menu' to see options available to you."
                        }
                    ])
                else:
                    # Admin summary card
                    summary_bubble = {
                        "type": "bubble",
                        "size": "mega",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "background": {
                                "type": "linearGradient",
                                "angle": "135deg",
                                "startColor": "#EF4444",
                                "endColor": "#991B1B"
                            },
                            "paddingAll": "20px",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "Admin Control Panel",
                                    "weight": "bold",
                                    "color": "#FFFFFF",
                                    "size": "md"
                                },
                                {
                                    "type": "text",
                                    "text": "Service Portal Overview",
                                    "color": "#FCA5A5",
                                    "size": "xxs",
                                    "margin": "xs"
                                }
                            ]
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "paddingAll": "16px",
                            "backgroundColor": "#F8FAFC",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": f"Hello, {user.full_name or 'Admin'}!",
                                    "weight": "bold",
                                    "size": "sm",
                                    "color": "#1E293B"
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "margin": "lg",
                                    "paddingAll": "12px",
                                    "backgroundColor": "#FEF2F2" if pending_count > 0 else "#ECFDF5",
                                    "cornerRadius": "md",
                                    "alignItems": "center",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "⏳" if pending_count > 0 else "✅",
                                            "size": "lg",
                                            "flex": 0
                                        },
                                        {
                                            "type": "box",
                                            "layout": "vertical",
                                            "margin": "md",
                                            "flex": 1,
                                            "contents": [
                                                {
                                                    "type": "text",
                                                    "text": "Pending Approval",
                                                    "weight": "bold",
                                                    "size": "xs",
                                                    "color": "#991B1B" if pending_count > 0 else "#065F46"
                                                },
                                                {
                                                    "type": "text",
                                                    "text": f"{pending_count} requests need review" if pending_count > 0 else "All caught up! No pending requests.",
                                                    "size": "xxs",
                                                    "color": "#EF4444" if pending_count > 0 else "#059669"
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "paddingAll": "12px",
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "uri",
                                        "label": "Review Pending Requests",
                                        "uri": f"{LIFF_URL}?page=admin"
                                    },
                                    "style": "primary",
                                    "color": "#EF4444" if pending_count > 0 else "#64748B",
                                    "height": "sm"
                                },
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "uri",
                                        "label": "View Portal Reports",
                                        "uri": f"{LIFF_URL}?page=reports"
                                    },
                                    "style": "link",
                                    "height": "sm"
                                }
                            ]
                        }
                    }

                    bubbles = [summary_bubble]
                    type_emojis = {
                        "room_booking": "🏢",
                        "vehicle_booking": "🚗",
                        "maintenance": "🔧",
                        "other": "📋"
                    }
                    for r in pending_requests:
                        requester_name = r.user.full_name or r.user.email if r.user else "Unknown User"
                        emoji = type_emojis.get(r.request_type, "📋")
                        time_str = "No time specified"
                        if r.start_time:
                            time_str = f"{r.start_time.strftime('%b %d, %H:%M')}"
                            if r.end_time:
                                time_str += f" - {r.end_time.strftime('%H:%M')}"
                        
                        req_bubble = {
                            "type": "bubble",
                            "size": "mega",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "background": {
                                    "type": "linearGradient",
                                    "angle": "135deg",
                                    "startColor": "#3B82F6",
                                    "endColor": "#1E40AF"
                                },
                                "paddingAll": "20px",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "Review Request",
                                        "weight": "bold",
                                        "color": "#FFFFFF",
                                        "size": "md"
                                    },
                                    {
                                        "type": "text",
                                        "text": f"Priority: {(r.priority or 'normal').upper()}",
                                        "color": "#BFDBFE",
                                        "size": "xxs",
                                        "margin": "xs"
                                    }
                                ]
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "16px",
                                "spacing": "md",
                                "backgroundColor": "#F8FAFC",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "spacing": "xs",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": f"{emoji} {r.title}",
                                                "weight": "bold",
                                                "size": "sm",
                                                "color": "#1E293B",
                                                "wrap": True
                                            },
                                            {
                                                "type": "text",
                                                "text": f"Requester: {requester_name}",
                                                "size": "xs",
                                                "color": "#64748B"
                                            },
                                            {
                                                "type": "text",
                                                "text": f"Time: {time_str}",
                                                "size": "xs",
                                                "color": "#64748B"
                                            }
                                        ]
                                    },
                                    {
                                        "type": "separator",
                                        "color": "#E2E8F0"
                                    },
                                    {
                                        "type": "text",
                                        "text": r.description or "No description provided.",
                                        "size": "xs",
                                        "color": "#475569",
                                        "wrap": True,
                                        "maxLines": 3
                                    }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "horizontal",
                                "spacing": "md",
                                "paddingAll": "12px",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "Approve",
                                            "data": f"action=approve&id={r.id}",
                                            "displayText": "Approving request..."
                                        },
                                        "style": "primary",
                                        "color": "#06C755",
                                        "height": "sm"
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "postback",
                                            "label": "Reject",
                                            "data": f"action=reject&id={r.id}",
                                            "displayText": "Rejecting request..."
                                        },
                                        "style": "primary",
                                        "color": "#EF4444",
                                        "height": "sm"
                                    }
                                ]
                            }
                        }
                        bubbles.append(req_bubble)

                    flex_payload = {
                        "type": "carousel",
                        "contents": bubbles
                    } if len(bubbles) > 1 else summary_bubble

                    await send_reply(reply_token, [
                        {
                            "type": "flex",
                            "altText": "Admin Review Summary",
                            "contents": flex_payload
                        }
                    ])
        elif event.get("type") == "postback":
            reply_token = event["replyToken"]
            line_user_id = event.get("source", {}).get("userId")
            postback_data = event.get("postback", {}).get("data", "")
            
            # Parse parameters
            params = {}
            for pair in postback_data.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    params[k] = v
            
            action = params.get("action")
            request_id_str = params.get("id")
            
            if action in ["approve", "reject"] and request_id_str:
                # 1. Verify admin permissions
                is_admin = False
                admin_user = None
                try:
                    from sqlalchemy import select
                    from app.db.session import async_session_local
                    from app.models.user import User
                    async with async_session_local() as db:
                        res = await db.execute(select(User).where(User.line_user_id == line_user_id))
                        admin_user = res.scalar_one_or_none()
                        if admin_user and admin_user.role == "admin":
                            is_admin = True
                except Exception as e:
                    print(f"Error checking admin: {e}")
                
                if not is_admin or not admin_user:
                    await send_reply(reply_token, [
                        {
                            "type": "text",
                            "text": "⚠️ Access Denied: Only administrators can approve or reject requests."
                        }
                    ])
                    continue
                
                # 2. Process status update
                new_status = "approved" if action == "approve" else "rejected"
                try:
                    from uuid import UUID
                    from app.services import admin_service
                    from app.core.cache import r as redis_client
                    
                    req_uuid = UUID(request_id_str)
                    
                    async with async_session_local() as db:
                        # Update status using the admin_service helper
                        result = await admin_service.update_request_status(
                            db, 
                            req_uuid, 
                            new_status, 
                            admin_user.id, 
                            f"Processed via LINE Chatbot by {admin_user.full_name or admin_user.email}"
                        )
                        
                        # Invalidate cache
                        try:
                            redis_client.delete(f"request:{req_uuid}")
                        except Exception:
                            pass
                        
                        # Fetch user details
                        from app.models.user import User
                        user_res = await db.execute(select(User).where(User.id == result.user_id))
                        user_obj = user_res.scalar_one_or_none()
                        user_name = (user_obj.full_name or user_obj.email) if user_obj else "Unknown"
                        user_email = user_obj.email if user_obj else "unknown"
                        
                        # Send webhook to n8n
                        try:
                            async with httpx.AsyncClient() as client:
                                await client.post(
                                    "http://localhost:5678/webhook/48c0cd3b-20d8-43c2-a4dc-e6b5dfd208f9",
                                    json={
                                        "event": "status_changed",
                                        "request_id": str(req_uuid),
                                        "status": new_status,
                                        "admin_note": f"Processed via LINE Chatbot by {admin_user.full_name or admin_user.email}",
                                        "user_id": str(result.user_id),
                                        "user_name": user_name,
                                        "user_email": user_email,
                                    },
                                    timeout=3.0
                                )
                        except Exception as ex:
                            print(f"Error sending n8n webhook: {ex}")
                        
                        # Enqueue LINE notification for the requester
                        try:
                            pool = request.app.state.arq_pool
                            status_messages = {
                                "approved": "✅ Your request has been approved.",
                                "rejected": "❌ Your request has been rejected.",
                            }
                            await pool.enqueue_job("send_notification", str(result.user_id), status_messages[new_status], str(req_uuid))
                        except Exception as ex:
                            print(f"Error enqueuing notification: {ex}")
                            
                    emoji = "✅" if new_status == "approved" else "❌"
                    await send_reply(reply_token, [
                        {
                            "type": "text",
                            "text": f"{emoji} Request successfully {new_status}!"
                        }
                    ])
                except Exception as ex:
                    await send_reply(reply_token, [
                        {
                            "type": "text",
                            "text": f"⚠️ Action failed: {str(ex)}"
                        }
                    ])

    return {"status": "ok"}
