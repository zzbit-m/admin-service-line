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

## Future Ideas

- Redis caching for request status queries
- Background task queue (future-ready)
- n8n webhook for additional event types
