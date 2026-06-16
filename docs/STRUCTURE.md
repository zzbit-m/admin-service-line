# Project Structure

```
project/
├── .env                          # Environment variables (DB URL, secret key, S3 credentials)
├── alembic.ini                   # Alembic configuration
├── requirements.txt              # Python dependencies
├── README.md                     # Setup instructions
├── alembic/
│   ├── __init__.py
│   ├── env.py                    # Alembic env — imports all models for autogenerate
│   ├── script.py.mako            # Migration template
│   └── versions/                 # Generated migration files
├── .env                          # Environment variables (DB URL, secret key, S3 credentials, LINE channel)
├── .certs/                       # Self-signed SSL certs for local HTTPS dev
├── alembic.ini                   # Alembic configuration
├── requirements.txt              # Python dependencies
├── liff-test.html                # LINE LIFF login test page
├── README.md                     # Setup instructions
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app, CORS, lifespan, router registration
│   ├── worker.py                 # ARQ WorkerSettings + send_notification LINE push job
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Pydantic Settings loaded from .env (DB, JWT, S3, Redis)
│   │   ├── security.py           # bcrypt hashing + JWT create/decode
│   │   ├── dependencies.py       # get_current_user / require_admin dependencies
│   │   ├── cache.py              # Redis connection (sync client, decode_responses=True)
│   │   ├── arq_pool.py           # create_arq_pool helper for ARQ lifecycle
│   │   └── storage.py            # boto3 S3 client and async upload_file helper
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py               # SQLAlchemy DeclarativeBase
│   │   └── session.py            # Async engine, session maker, get_db generator
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py               # User (id, email, full_name, hashed_password, role, line_user_id, is_active)
│   │   ├── resource.py           # Resource (id, name, type, description, is_active)
│   │   ├── request.py            # ServiceRequest (id, user_id, resource_id, title, status, times, admin_note)
│   │   └── attachment.py         # Attachment (id, request_id, file_url, filename, uploaded_by)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py               # RegisterRequest, LoginRequest, AuthResponse
│   │   ├── resource.py           # ResourceCreate/Update/Response (Literal type validation)
│   │   ├── request.py            # RequestCreate, StatusUpdate (Literal), RequestResponse
│   │   └── attachment.py         # AttachmentResponse
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py               # POST /auth/register, /auth/login
│   │   ├── auth_line.py          # POST /auth/line (LINE LIFF login)
│   │   ├── requests.py           # POST /requests, GET /requests/me, PATCH /requests/{id}/cancel, GET /requests/{id}
│   │   ├── admin.py              # Admin CRUD for requests/resources, n8n webhook on status change, Redis cache invalidation
│   │   └── attachments.py        # POST/GET /requests/{id}/attachments
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py       # Register + login logic
│       ├── request_service.py    # User request CRUD, cancel, time conflict check
│       ├── admin_service.py      # Admin request/resource management, status transitions
│       └── attachment_service.py # File upload validation, S3 upload, attachment listing
└── docs/
    ├── ARCHITECTURE.md           # System flow, stack, layer responsibilities
    ├── API_SPEC.md               # All endpoints with request/response shapes
    ├── STRUCTURE.md              # This file
    └── PROJECT_PLAN.md           # Phased roadmap
```
