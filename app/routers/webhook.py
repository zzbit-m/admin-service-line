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

            if text in ["hi", "hello", "hey", "menu", "help", "start", "home", "book", "booking", "สวัสดี", "เมนู"]:
                await send_reply(reply_token, [
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
                                    "startColor": "#06C755",
                                    "endColor": "#04964A"
                                },
                                "paddingAll": "24px",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "Service Portal",
                                        "weight": "bold",
                                        "color": "#ffffff",
                                        "size": "xl"
                                    },
                                    {
                                        "type": "text",
                                        "text": "Booking & Request Management",
                                        "color": "#C8F5D8",
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
                                        "text": "Hi there! What would you like to do?",
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
                                        "contents": [
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
                                                                "text": "Book a room, vehicle, or report an issue",
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
                                            },
                                            {
                                                "type": "box",
                                                "layout": "horizontal",
                                                "backgroundColor": "#F8FAFC",
                                                "paddingAll": "14px",
                                                "cornerRadius": "lg",
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
                                                                "text": "My Profile",
                                                                "weight": "bold",
                                                                "size": "sm",
                                                                "color": "#334155"
                                                            },
                                                            {
                                                                "type": "text",
                                                                "text": "View or update your account info",
                                                                "size": "xxs",
                                                                "color": "#64748B",
                                                                "wrap": True
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": ">",
                                                        "size": "lg",
                                                        "color": "#CBD5E1",
                                                        "flex": 0,
                                                        "align": "end"
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
                                "paddingAll": "14px",
                                "backgroundColor": "#F8FAFC",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "Tip: You can type \"hi\" anytime to see this again.",
                                        "size": "xxs",
                                        "color": "#94A3B8",
                                        "align": "center"
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
                        "text": "Hey! I didn't quite get that.\n\nTry saying \"hi\" or \"help\" and I'll show you what I can do!",
                        "quickReply": {
                            "items": [
                                {
                                    "type": "action",
                                    "action": {
                                        "type": "message",
                                        "label": "Show Options",
                                        "text": "hi"
                                    }
                                },
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

    return {"status": "ok"}
