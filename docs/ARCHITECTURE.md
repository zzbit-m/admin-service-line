# Architecture

## Tech Stack

- **Runtime:** Python 3.11
- **Framework:** FastAPI
- **Database:** PostgreSQL 15
- **ORM:** Async SQLAlchemy 2.0 with asyncpg driver
- **Validation:** Pydantic v2
- **Auth:** python-jose (JWT) + passlib[bcrypt]
- **Migrations:** Alembic

## System Flow

```
Client → HTTP Request → FastAPI Router → Service Layer → SQLAlchemy → PostgreSQL
                              ↕
                         Dependencies
                      (auth / admin check)
```

1. Request hits router endpoint with optional `Authorization: Bearer <token>` header
2. Dependencies (`get_current_user`, `require_admin`) decode JWT and fetch user from DB
3. Router delegates to service function
4. Service performs business logic and DB operations via async session
5. Response returned as Pydantic schema

## Layer Responsibilities

| Layer | Role |
|-------|------|
| `routers/` | HTTP routing, input parsing, status codes, no logic |
| `services/` | Business logic, DB queries, raises HTTPException on errors |
| `schemas/` | Pydantic models for request/response validation |
| `models/` | SQLAlchemy ORM models mapping to DB tables |
| `core/` | Config, JWT/密码 utilities, FastAPI dependencies |
| `db/` | Engine, session factory, declarative base |

## Auth Flow

- Register/Login return `{"access_token": "...", "token_type": "bearer"}`
- Protected endpoints read token from `Authorization: Bearer <token>`
- `get_current_user` decodes JWT, fetches user, raises 401 if invalid
- `require_admin` wraps `get_current_user`, raises 403 if role != admin

## Error Mapping

| Status | When |
|--------|------|
| 400 | Validation error or duplicate email |
| 401 | Missing/invalid token or bad credentials |
| 403 | User lacks admin role |
| 404 | Resource or request not found |
