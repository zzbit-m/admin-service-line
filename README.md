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

- API runs at `http://localhost:8000`
- Docs at `http://localhost:8000/docs`

