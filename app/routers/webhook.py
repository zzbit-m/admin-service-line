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
                        "type": "text",
                        "text": "Hello! Welcome to the Service Portal. Please choose an action below to get started: 😊"
                    },
                    {
                        "type": "flex",
                        "altText": "⚡ Service Portal Menu",
                        "contents": {
                            "type": "bubble",
                            "size": "mega",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "paddingAll": "24px",
                                "spacing": "lg",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "⚡ Service Portal",
                                                "weight": "bold",
                                                "size": "xl",
                                                "color": "#111827",
                                                "flex": 1
                                            }
                                        ]
                                    },
                                    {
                                        "type": "text",
                                        "text": "Manage bookings, view requests, and update your profile directly from LINE.",
                                        "size": "xs",
                                        "color": "#6B7280",
                                        "wrap": True
                                    },
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "spacing": "md",
                                        "contents": [
                                            {
                                                "type": "box",
                                                "layout": "horizontal",
                                                "backgroundColor": "#F3F4F6",
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
                                                                "color": "#1F2937"
                                                            },
                                                            {
                                                                "type": "text",
                                                                "text": "View and track active requests",
                                                                "size": "xxs",
                                                                "color": "#4B5563"
                                                            }
                                                        ]
                                                    }
                                                ]
                                            },
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
                                                "backgroundColor": "#F3F4F6",
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
                                                                "color": "#1F2937"
                                                            },
                                                            {
                                                                "type": "text",
                                                                "text": "Manage your profile details",
                                                                "size": "xxs",
                                                                "color": "#4B5563"
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
