# Admin Service Portal

A role-based service request administration portal with backend APIs, LINE authentication, file attachments, and a React frontend.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Run the App](#run-the-app)
- [LINE Development](#line-development)
- [Useful Scripts](#useful-scripts)
- [API Overview](#api-overview)
- [Documentation](#documentation)
- [License](#license)

## Overview

This repository contains the backend and frontend for the Admin Service Portal. It supports:

- user and admin request workflows
- request approval and rejection
- file attachments
- LINE LIFF login and webhook integration
- background processing with Redis/ARQ
- resource management and admin reporting

## Features

- Request submission, listing, and detail view
- Admin request review and status updates
- JWT and LINE authentication
- Attachment upload and resource management
- Redis caching and asynchronous worker processing
- React + Vite frontend with admin/user views
- Local dev automation via PowerShell scripts

## Tech Stack

- Backend: FastAPI, Python 3.11, Async SQLAlchemy, Alembic
- Database: PostgreSQL 15
- Cache/Queue: Redis + ARQ
- Storage: MinIO / S3-compatible file storage via boto3
- Auth: JWT, LINE Login (LIFF), LINE Messaging API
- Frontend: React, TypeScript, Vite

## Prerequisites

- Python 3.11+
- PostgreSQL 15
- Redis
- MinIO or S3-compatible storage
- Node.js + npm/yarn for frontend development
- Optional: `cloudflared` for LINE webhook tunneling

## Setup

1. Clone repository

```bash
git clone https://github.com/zzbit-m/admin-service-line.git
cd "ADMIN SERVICE PORTAL"
```

2. Create and activate a Python virtual environment

```bash
python -m venv venv
# Windows PowerShell
env\Scripts\Activate.ps1
# macOS / Linux
# source venv/bin/activate
```

3. Install backend dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables

- Copy `.env` from your template or create it manually
- Set `DATABASE_URL`, `SECRET_KEY`, `REDIS_HOST`, `REDIS_PORT`, and LINE credentials

5. Create PostgreSQL database

```sql
CREATE DATABASE admin_portal;
```

6. Run database migrations

```bash
alembic upgrade head
```

## Run the App

### Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

The API will be available at `http://localhost:8001` and docs at `http://localhost:8001/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Worker

```bash
python -m arq app.worker.WorkerSettings
```

## LINE Development

1. Start the backend on port `8001`
2. Expose it using `cloudflared tunnel --url http://localhost:8001`
3. Update LINE Console settings:
   - LIFF endpoint: `https://<tunnel-url>/liff-app.html`
   - Webhook URL: `https://<tunnel-url>/webhook/line`
4. Open the LIFF app URL in browser

### Dev mode without LINE

For local testing, append `?dev=1` to the LIFF URL:

```text
http://localhost:8001/liff-app.html?dev=1
```

This enables a local switch mode that bypasses LINE login and uses development credentials.

## Useful Scripts

- Start all services: `.
un.ps1` or `.
un.ps1` if available
- Stop all services: `.
un.ps1` or `.
un.ps1` if available
- Promote admin user:

```bash
python scripts/promote_admin.py <email>
```

- Seed development accounts:

```bash
python scripts/seed_dev_accounts.py
```

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and receive JWT |
| POST | `/auth/line` | Login via LINE access token |
| GET | `/requests/me` | List current user requests |
| POST | `/requests` | Create a new request |
| GET | `/requests/{id}` | Get request detail |
| PATCH | `/requests/{id}/cancel` | Cancel a pending request |
| POST | `/requests/{id}/attachments` | Upload attachment |
| GET | `/requests/{id}/attachments` | List attachments for a request |
| GET | `/admin/requests` | List all requests (admin) |
| GET | `/admin/requests/{id}` | Get admin request detail |
| PATCH | `/admin/requests/{id}/status` | Update request status |
| GET | `/admin/resources` | List resources (admin) |
| POST | `/admin/resources` | Create a new resource |

## Documentation

Additional project documentation is available in the `docs/` folder:

- `docs/API_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_GUIDE.md`
- `docs/PROJECT_PLAN.md`
- `docs/STRUCTURE.md`

## License

This project is licensed under the terms in `LICENSE`.
