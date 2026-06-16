# Admin Service Portal

Internal backend for managing service requests and resources with role-based access control.

## Stack

- FastAPI + Python 3.11
- PostgreSQL 15
- Async SQLAlchemy + asyncpg
- MinIO (S3-compatible file storage via boto3)
- Pydantic v2
- JWT auth (python-jose + bcrypt)
- Alembic migrations
- Redis (cache + ARQ job queue)
- LINE LIFF + Messaging API

---

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

---

## PowerShell Automation (Recommended)

To start the entire application suite (Docker dependencies, database migrations, backend, worker, proxy, and Cloudflare tunnel) automatically in separate windows:
```powershell
.\start.ps1
```
*Note: The script automatically copies the generated Cloudflare LINE Webhook URL to your clipboard for quick pasting!*

To stop all services and containers cleanly:
```powershell
.\stop.ps1
```

---

## LINE Login (Dev)

1. Start backend: `uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload`
2. Expose via cloudflared: `cloudflared tunnel --url http://localhost:8001`
3. Update LIFF endpoint URL in LINE Console to `https://<tunnel-url>/liff-app.html`
4. Update Messaging API Webhook URL to `https://<tunnel-url>/webhook/line`
5. Open `https://<tunnel-url>/liff-app.html` in browser
6. LINE profile `displayName` is stored in `full_name` column on users table

### Dev Switch Mode (Testing without LINE)

The LIFF app includes a **Switch Mode** button in the header for local testing — it lets you toggle between User and Admin views without going through LINE login.

Activate it by appending `?dev=1` to the URL:

```
http://localhost:8001/liff-app.html?dev=1
```

In dev mode, the app skips LIFF init and logs in using pre-seeded test credentials defined in `public/liff-app.html`. Use the **⇄ Switch** button in the header to toggle between user and admin roles.

---

## Background Worker (ARQ)

Run the ARQ worker to process LINE push notifications:

```bash
python -m arq app.worker.WorkerSettings
```

The worker reads Redis config from `.env` (`REDIS_HOST` / `REDIS_PORT`) and connects to the same PostgreSQL database to look up `line_user_id` before sending push messages via LINE Messaging API.

---

## Promote Admin

Grant admin role to an existing user:

```bash
python scripts/promote_admin.py <email>
```

---

## Progress

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Auth (register/login), request CRUD, admin role, resources | ✅ Done |
| 2 | Status transitions, time conflict detection, cancel, pagination | ✅ Done |
| 3 | File attachments via MinIO S3, Redis cache for resources | ✅ Done |
| 4 | n8n webhook on status changes, LINE login via LIFF | ✅ Done |
| 5 | LINE `displayName` stored in `full_name` column | ✅ Done |
| 6 | Redis cache for request status, ARQ worker scaffold | ✅ Done |
| 7 | LINE push notifications via ARQ on approve/reject/cancel | ✅ Done |
| 8 | n8n webhooks for request_created and request_cancelled events | ✅ Done |
| 9 | Full LIFF app rewrite — user + admin views, `request_type` field | ✅ Done |
| 10 | Comments section, Resource UI, Reports, and Front-End Booking | ✅ Done |
| 11 | PowerShell automation scripts (`start.ps1` and `stop.ps1`) | ✅ Done |

---

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login (returns JWT) |
| POST | `/auth/line` | Login via LINE access token |
| GET | `/requests/me` | List my requests |
| POST | `/requests` | Create a request |
| GET | `/requests/{id}` | Get request detail |
| PATCH | `/requests/{id}/cancel` | Cancel a pending request |
| POST | `/requests/{id}/attachments` | Upload attachment |
| GET | `/requests/{id}/attachments` | List attachments |
| GET | `/admin/requests` | List all requests (admin) |
| GET | `/admin/requests/{id}` | Get request detail (admin) |
| PATCH | `/admin/requests/{id}/status` | Approve / reject (admin) |
| GET | `/admin/resources` | List resources (cached) |
| POST | `/admin/resources` | Create resource (admin) |
