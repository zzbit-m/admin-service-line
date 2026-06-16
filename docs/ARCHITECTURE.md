# Architecture

## Tech Stack

- **Runtime:** Python 3.11
- **Framework:** FastAPI
- **Database:** PostgreSQL 15
- **ORM:** Async SQLAlchemy 2.0 with asyncpg driver
- **Validation:** Pydantic v2
- **Auth:** python-jose (JWT) + passlib[bcrypt], LINE LIFF OAuth
- **Migrations:** Alembic
- **File Storage:** MinIO via S3-compatible API (boto3)
- **Cache:** Redis (sync client for cache-aside pattern)
- **HTTP Client:** httpx (n8n webhook, LINE token verification)

## System Flow

```
Client → HTTP Request → FastAPI Router → Service Layer → SQLAlchemy → PostgreSQL
                              ↕                    ↕            ↕         ↕
                         Dependencies      Redis (cache)    httpx    boto3 → MinIO (S3)
                       (auth / admin)          ↕             ↕
                                           resource list   n8n webhook
                                                           LINE API
```

1. Request hits router endpoint with optional `Authorization: Bearer <token>` header
2. Dependencies (`get_current_user`, `require_admin`) decode JWT and fetch user from DB
3. Router delegates to service function
4. Service performs business logic — DB operations via async session, file uploads via boto3 to MinIO, HTTP calls via httpx
5. Response returned as Pydantic schema

## Layer Responsibilities

| Layer | Role |
|-------|------|
| `routers/` | HTTP routing, input parsing, status codes, no logic |
| `services/` | Business logic, DB queries, file upload orchestration, raises HTTPException |
| `schemas/` | Pydantic models for request/response validation |
| `models/` | SQLAlchemy ORM models mapping to DB tables |
| `core/` | Config, JWT/password utilities, FastAPI dependencies, boto3 S3 client, Redis connection |
| `db/` | Engine, session factory, declarative base |

## Auth Flow

### Email/Password
- Register/Login return `{"access_token": "...", "token_type": "bearer"}`
- Protected endpoints read token from `Authorization: Bearer <token>`
- `get_current_user` decodes JWT, fetches user, raises 401 if invalid
- `require_admin` wraps `get_current_user`, raises 403 if role != admin

### LINE LIFF
1. LIFF app calls `liff.login()` → user authorizes via LINE app
2. LIFF SDK returns an access token via `liff.getAccessToken()`
3. Client sends `{"access_token": "..."}` to `POST /auth/line`
4. Server verifies token with LINE API (`/oauth2/v2.1/verify` and `/v2/profile`)
5. Server looks up user by `line_user_id` or auto-creates a new user with `line_<id>@line.local` email and `displayName` stored in `full_name`
6. Server issues a standard JWT — subsequent requests use `Authorization: Bearer` as normal

## File Upload Flow

1. Client sends multipart POST with file to `/requests/{id}/attachments`
2. Router validates auth via `get_current_user`
3. Service checks request ownership, validates file type (jpeg/png/gif/pdf) and size (max 5MB)
4. Service calls `storage.upload_file()` which uses boto3 to upload to MinIO with a UUID filename
5. `Attachment` record saved to DB with the returned S3 URL
6. Response returns `AttachmentResponse` schema

## Caching Strategy

- **`GET /admin/resources`** — cache-aside pattern with Redis, key `resources:all`, TTL 60 seconds
- Cache invalidated (`r.delete`) on `POST /admin/resources` and `PATCH /admin/resources/{id}`
- **`GET /requests/{id}`** — cache-aside pattern with Redis, key `request:{id}`, TTL 30 seconds
- Cache invalidated (`r.delete`) on `PATCH /requests/{id}/cancel` and `PATCH /admin/requests/{id}/status`
- Serialized as JSON via Pydantic's `model_dump(mode="json")` for correct UUID/datetime handling
- Redis host/port configurable via `REDIS_HOST` / `REDIS_PORT` in `.env` (defaults: `localhost:6379`)

## n8n Webhook Integration

- On `PATCH /admin/requests/{id}/status`, after the status update succeeds, a fire-and-forget POST is sent to the n8n webhook
- Payload: `{"request_id": "<uuid>", "status": "approved|rejected", "admin_note": "<string>"}`
- Target: `http://localhost:5678/webhook-test/<uuid>`
- Failures are silently caught (`try/except`) so a down webhook never blocks the status update

## Background Worker (ARQ)

- ARQ (async Redis Queue) runs lightweight background jobs via Redis
- `app/worker.py` defines `WorkerSettings` and the `send_notification` job function
- `app/core/arq_pool.py` provides `create_arq_pool()` for the FastAPI lifespan to open/close a pool connection
- Jobs are enqueued from router endpoints via `app.state.arq_pool.enqueue_job("function_name", *args)`
- Run separately: `python -m arq app.worker.WorkerSettings`

### LINE Push Notification Flow

1. Admin approves/rejects a request → `PATCH /admin/requests/{id}/status` enqueues `send_notification`
2. User cancels own request → `PATCH /requests/{id}/cancel` enqueues `send_notification`
3. ARQ worker picks up the job and queries the user's `line_user_id` from PostgreSQL
4. If `line_user_id` is set, worker sends `POST https://api.line.me/v2/bot/message/push` with the message text
5. If `line_user_id` is `null` (email-only user), worker skips silently
6. All failures are caught and logged with `print()` — never crash the worker

## Status Transition Rules

| Current Status | Allowed Transitions |
|----------------|---------------------|
| pending | approved, rejected |
| approved | cancelled |
| rejected | (terminal) |
| cancelled | (terminal) |

Invalid transitions return 400 with a descriptive message.

## Error Mapping

| Status | When |
|--------|------|
| 400 | Validation error, duplicate email, invalid file type/size, invalid status transition |
| 401 | Missing/invalid token or bad credentials |
| 403 | User lacks admin role |
| 404 | Resource, request, or attachment target not found |
| 409 | Resource time slot conflict on request creation |
