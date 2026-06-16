import hashlib
import hmac
import base64
import httpx
from fastapi import APIRouter, Request, HTTPException
from app.core.config import settings

router = APIRouter()

LIFF_URL = f"https://liff.line.me/{settings.LINE_LIFF_ID}"

async def send_reply(reply_token: str, messages: list):
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.line.me/v2/bot/message/reply",
            headers={"Authorization": f"Bearer {settings.LINE_MESSAGING_ACCESS_TOKEN}"},
            json={"replyToken": reply_token, "messages": messages}
        )

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

            if text in ["hi", "hello", "menu", "help", "สวัสดี", "เมนู"]:
                await send_reply(reply_token, [
                    {
                        "type": "flex",
                        "altText": "⚡ Booking & Requests Menu",
                        "contents": {
                            "type": "bubble",
                            "size": "mega",
                            "header": {
                                "type": "box",
                                "layout": "vertical",
                                "background": {
                                    "type": "linearGradient",
                                    "angle": "135deg",
                                    "startColor": "#06C755",
                                    "endColor": "#05A847"
                                },
                                "paddingAll": "20px",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "Booking & Requests",
                                        "weight": "bold",
                                        "color": "#ffffff",
                                        "size": "xl"
                                    },
                                    {
                                        "type": "text",
                                        "text": "Service Portal",
                                        "color": "#E8FAF0",
                                        "size": "xs",
                                        "margin": "xs"
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
                                        "text": "Select an action below to get started: 👇",
                                        "weight": "bold",
                                        "size": "sm",
                                        "color": "#1E2937"
                                    },
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "spacing": "sm",
                                        "contents": [
                                            {
                                                "type": "box",
                                                "layout": "horizontal",
                                                "backgroundColor": "#E8FAF0",
                                                "paddingAll": "12px",
                                                "cornerRadius": "md",
                                                "action": {
                                                    "type": "uri",
                                                    "label": "New Request",
                                                    "uri": f"{LIFF_URL}?page=new"
                                                },
                                                "alignItems": "center",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": "➕",
                                                        "size": "lg",
                                                        "flex": 0,
                                                        "margin": "none"
                                                    },
                                                    {
                                                        "type": "box",
                                                        "layout": "vertical",
                                                        "margin": "md",
                                                        "contents": [
                                                            {
                                                                "type": "text",
                                                                "text": "New Request",
                                                                "weight": "bold",
                                                                "size": "sm",
                                                                "color": "#047857"
                                                            },
                                                            {
                                                                "type": "text",
                                                                "text": "Book rooms, vehicles, or log issues",
                                                                "size": "xxs",
                                                                "color": "#065F46"
                                                            }
                                                        ]
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "box",
                                                "layout": "horizontal",
                                                "backgroundColor": "#EFF6FF",
                                                "paddingAll": "12px",
                                                "cornerRadius": "md",
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
                                                        "size": "lg",
                                                        "flex": 0,
                                                        "margin": "none"
                                                    },
                                                    {
                                                        "type": "box",
                                                        "layout": "vertical",
                                                        "margin": "md",
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
                                                                "text": "View and track active requests",
                                                                "size": "xxs",
                                                                "color": "#3B82F6"
                                                            }
                                                        ]
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "box",
                                                "layout": "horizontal",
                                                "backgroundColor": "#F8FAFC",
                                                "paddingAll": "12px",
                                                "cornerRadius": "md",
                                                "action": {
                                                    "type": "uri",
                                                    "label": "My Profile",
                                                    "uri": f"{LIFF_URL}?page=profile"
                                                },
                                                "alignItems": "center",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": "👤",
                                                        "size": "lg",
                                                        "flex": 0,
                                                        "margin": "none"
                                                    },
                                                    {
                                                        "type": "box",
                                                        "layout": "vertical",
                                                        "margin": "md",
                                                        "contents": [
                                                            {
                                                                "type": "text",
                                                                "text": "My Profile",
                                                                "weight": "bold",
                                                                "size": "sm",
                                                                "color": "#334155"
                                                            },
                                                            {
                                                                "type": "text",
                                                                "text": "Manage your profile details",
                                                                "size": "xxs",
                                                                "color": "#64748B"
                                                            }
                                                        ]
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                ])
            else:
                await send_reply(reply_token, [
                    {
                        "type": "text",
                        "text": "Type 'menu' to see available options. 😊"
                    }
                ])

    return {"status": "ok"}
