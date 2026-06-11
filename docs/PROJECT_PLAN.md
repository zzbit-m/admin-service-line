# Project Plan

## Overview

Internal Admin Service Portal — backend for managing service requests and resources with role-based access control.

## Stack

- FastAPI + Python 3.11
- PostgreSQL 15
- Async SQLAlchemy + asyncpg
- Pydantic v2
- JWT auth (python-jose + bcrypt)
- Alembic migrations

---

## Phase 1 — Complete ✅

User authentication (register/login with JWT), service request CRUD for users, admin role with request/resource management.

### What was built

- User registration and login with bcrypt hashing and JWT tokens
- Authenticated user endpoints: create request, list own requests, get request by ID
- Admin endpoints: list all requests (with status filter), update request status, CRUD resources
- Pydantic v2 schemas with `Literal` type constraints for status and resource type
- Proper error codes: 400/401/403/404
- Alembic migrations configured with all models imported for autogenerate
- Lifespan handler for clean engine disposal on shutdown

---

## Phase 2 — Planned

Things to add in future phases:

- Pagination for list endpoints
- LINE Messaging API integration (webhook, reply messages)
- Request cancellation by user
- Email notifications on status change
- Audit log for admin actions
- Rate limiting
- API key management for external integrations
- Unit and integration tests
- CI/CD pipeline
- Deployment configuration
