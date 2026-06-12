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
                        "type": "template",
                        "altText": "Admin Service Portal Menu",
                        "template": {
                            "type": "buttons",
                            "text": "Admin Service Portal\nWhat would you like to do?",
                            "actions": [
                                {
                                    "type": "uri",
                                    "label": "📋 My Requests",
                                    "uri": f"{LIFF_URL}?page=requests"
                                },
                                {
                                    "type": "uri",
                                    "label": "➕ New Request",
                                    "uri": f"{LIFF_URL}?page=new"
                                },
                                {
                                    "type": "uri",
                                    "label": "👤 My Profile",
                                    "uri": f"{LIFF_URL}?page=profile"
                                }
                            ]
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
