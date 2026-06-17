# Project Plan

## Overview

Internal Admin Service Portal — backend for managing service requests and resources with role-based access control.

## Stack

- FastAPI + Python 3.11
- PostgreSQL 15
- Async SQLAlchemy + asyncpg
- MinIO (S3-compatible file storage via boto3)
- Pydantic v2
- JWT auth (python-jose + bcrypt)
- Alembic migrations

---

## Phase 1 — Complete ✅

Auth (register/login), user request CRUD, admin role, resource management.

Includes: JWT auth, bcrypt hashing, role-based access (user/admin), Pydantic Literal constraints, Alembic setup, lifespan handler.

---

## Phase 2 — Complete ✅

Status transition enforcement, time conflict detection, user cancel endpoint, pagination.

Includes: `VALID_TRANSITIONS` map, `start_time`/`end_time` columns on service_requests, overlap check on create (409), `PATCH /requests/{id}/cancel`, `skip`/`limit` on list endpoints.

---

## Phase 3 — Complete ✅

File attachment upload via S3-compatible MinIO storage, Redis cache layer for resource list.

Includes: `Attachment` model, boto3 S3 client with `run_in_executor`, file type/size validation (5MB max), `POST /requests/{id}/attachments` (201), `GET /requests/{id}/attachments`. Redis cache-aside on `GET /admin/resources` with TTL 60s and invalidation on create/update.

---

## Phase 4 — Complete ✅

n8n webhook integration on admin status changes, LINE login via LIFF.

Includes: `httpx.AsyncClient` POST to n8n webhook on approve/reject (silent failure), `POST /auth/line` endpoint with LINE token verification and auto-provisioning, LIFF test page (`liff-test.html`), `REDIS_HOST`/`REDIS_PORT` moved to `Settings` config.

---

## Phase 5 — Complete ✅

LINE login stores `displayName` from LINE profile into `full_name` column on users table.

Includes: `full_name` column added to User model (`String(255)`, nullable), Alembic migration `add_full_name_to_users`, `POST /auth/line` INSERT updated to include `full_name` param from LINE profile response.

---

## Phase 6 — Complete ✅

Redis cache for request status queries + ARQ background worker scaffold.

Includes: Cache-aside on `GET /requests/{id}` with TTL 30s and invalidation on approve/reject/cancel. ARQ worker scaffold with `WorkerSettings`, `create_arq_pool` helper, lifespan wiring, and `send_notification` placeholder.

---

## Phase 7 — Complete ✅

LINE push notifications via ARQ worker on status changes.

Includes: `send_notification` implementation queries user's `line_user_id` and sends LINE push message via Messaging API. Enqueues on approve (admin), reject (admin), and cancel (user). Silent failure on missing `line_user_id` or worker not running.

---

## Phase 8 — Complete ✅

n8n webhook extended to three event types with `event` discriminator field.

Includes: `"event": "status_changed"` added to existing approve/reject webhook payload. New webhook fire on `POST /requests` (`"event": "request_created"`) and `PATCH /requests/{id}/cancel` (`"event": "request_cancelled"`). All new calls use `timeout=3.0`. Silent failure on all webhook calls. Webhook URL uses `/webhook/` (production) instead of `/webhook-test/` (dev).

---

## Phase 9 — Complete ✅

Full LIFF app rewrite with user + admin views and `request_type` field.

Includes: `request_type` column on `ServiceRequest` model (Enum: room_booking, vehicle_booking, maintenance, other), Alembic migration, schema updates. LIFF app now detects role from JWT and shows user dashboard (my requests, detail, new request with type dropdown, cancel) or admin dashboard (pending/all tabs, approve/reject with admin note). Status badges with proper colors, request type badges, mobile-first design.

## Phase 10 — Complete ✅

Comments section, Resource UI, Reports, and Front-End Booking.

Includes: `RequestComment` database models, migrations, schemas, and endpoints for request discussion. Adds admin Reports / Stats dashboard and Resource management UI. Integrates resource select dropdowns, dates, and times inside user's "New Request" page with dynamic check of occupied slots (`GET /resources/{id}/availability`) and client-side overlapping time-slot conflict validations.

## Phase 11 — Complete ✅

PowerShell automation scripts for starting/stopping services.

Includes: `start.ps1` and `stop.ps1` scripts to automate starting Docker dependencies (db, redis, minio, n8n), running database migrations, opening separate terminal windows for FastAPI/ARQ worker/Proxy server, running Cloudflare quick tunnel in background, automatically parsing its logs to copy the webhook URL to the clipboard, and stopping everything cleanly.

---

## Phase 12 — Complete ✅

Resource Deletion in Admin Panel.

Includes: `delete_resource` helper in `admin_service.py` to decouple requests from deleted resources (nullify foreign key) without breaking historical audit trails, corresponding `DELETE /admin/resources/{id}` route with Redis cache invalidation, custom FormSheet deletion callback trigger in UI, and full deletion confirmation flow.

---

## Phase 13 — Complete ✅

LINE Chatbot and Portal/LIFF UI Enhancements.

Includes: Custom greeting screens & Flex menus depending on user role (crimson/admin vs green/user theme), support for postback webhook callback events allowing direct inline approvals and rejection carousels in chat, browser-persisted Premium Dark Mode toggling via CSS custom properties, graphical horizontal Daily Schedule timeline bar visualizer inside resource selection details, and real-time LINE bot profile displayName fetch & sync with Postgres users to resolve default ID values.

---

## Future Ideas

- *(none)*

