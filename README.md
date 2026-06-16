# Admin Service Portal

Internal backend for managing service requests and resources.

## Setup

1. Install Python 3.11+
2. Create a PostgreSQL 15 database named `admin_portal`
3. Copy `.env` and update `DATABASE_URL` with your credentials
4. Change `SECRET_KEY` in `.env` to a secure random value

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Defaults

- API runs at `http://localhost:8001`
- Docs at `http://localhost:8001/docs`

## LINE Login (Dev)

1. Start backend: `uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload`
2. Expose via cloudflared: `cloudflared tunnel --url http://localhost:8001`
3. Update LIFF endpoint URL in LINE Console to `https://<tunnel-url>/liff-app.html`
4. Update Messaging API Webhook URL to `https://<tunnel-url>/webhook/line`
5. Open `https://<tunnel-url>/liff-app.html` in browser
6. LINE profile `displayName` is stored in `full_name` column on users table

## Background Worker (ARQ)

Run the ARQ worker to process LINE push notifications:

```bash
python -m arq app.worker.WorkerSettings
```

The worker reads Redis config from `.env` (`REDIS_HOST` / `REDIS_PORT`) and connects to the same PostgreSQL database to look up `line_user_id` before sending push messages via LINE Messaging API.

