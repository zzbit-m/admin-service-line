# Project Structure

```
project/
├── .certs/                       # Self-signed SSL certs for local HTTPS dev
├── .env                          # Environment variables (DB URL, secret key, S3 credentials, LINE channel)
├── alembic.ini                   # Alembic configuration
├── requirements.txt              # Python dependencies
├── README.md                     # Setup instructions
├── start.ps1                     # PowerShell quickstart script
├── stop.ps1                      # PowerShell shutdown script
├── docker-compose.yml            # Docker services definition (Postgres, Redis, MinIO, n8n)
├── Dockerfile                    # Docker build configuration
├── alembic/
│   ├── env.py                    # Alembic env — imports all models for autogenerate
│   ├── script.py.mako            # Migration template
│   └── versions/                 # Generated migration files
├── app/
│   ├── main.py                   # FastAPI app, CORS, lifespan, router registration
│   ├── worker.py                 # ARQ WorkerSettings + send_notification LINE push job
│   ├── core/
│   │   ├── config.py             # Pydantic Settings loaded from .env (DB, JWT, S3, Redis)
│   │   ├── security.py           # bcrypt hashing + JWT create/decode
│   │   ├── dependencies.py       # get_current_user / require_admin dependencies
│   │   ├── cache.py              # Redis connection (sync client, decode_responses=True)
│   │   ├── arq_pool.py           # create_arq_pool helper for ARQ lifecycle
│   │   └── storage.py            # boto3 S3 client and async upload_file helper
│   ├── db/
│   │   ├── base.py               # SQLAlchemy DeclarativeBase
│   │   └── session.py            # Async engine, session maker, get_db generator
│   ├── models/
│   │   ├── user.py               # User db model
│   │   ├── resource.py           # Resource db model
│   │   ├── request.py            # ServiceRequest db model
│   │   └── attachment.py         # Attachment db model
│   ├── schemas/
│   │   ├── auth.py               # RegisterRequest, LoginRequest, AuthResponse schemas
│   │   ├── resource.py           # Resource schemas (with literal type validations)
│   │   ├── request.py            # Request schemas
│   │   └── attachment.py         # AttachmentResponse schema
│   ├── routers/
│   │   ├── auth.py               # Register/Login endpoints
│   │   ├── auth_line.py          # LINE LIFF login endpoint
│   │   ├── requests.py           # User request CRUD endpoints
│   │   ├── admin.py              # Admin CRUD, n8n webhook triggers, Redis cache invalidation
│   │   └── attachments.py        # Attachment upload/list endpoints
│   └── services/
│       ├── auth_service.py       # User registration + login business logic
│       ├── request_service.py    # Request CRUD & conflict-checking logic
│       ├── admin_service.py      # Admin status change & resources logic
│       └── attachment_service.py # Attachment S3 upload & validation logic
├── public/                       # Static public assets
│   ├── liff-app.html             # Main LINE LIFF frontend application (User + Admin UI)
│   └── liff-test.html            # LIFF login verification / test page
├── scripts/                      # Developer utility and CLI scripts
│   ├── list_users.py             # Prints users in PostgreSQL
│   ├── promote_admin.py          # Grant admin role to user by email/LINE ID
│   ├── proxy_server.py           # Local development proxy server (port 3000)
│   └── seed_dev_accounts.py      # Seeds test credentials for dev environments
└── docs/
    ├── ARCHITECTURE.md           # System architecture design & components responsibilities
    ├── API_SPEC.md               # Backend API specification (endpoints shapes)
    ├── STRUCTURE.md              # This file
    └── PROJECT_PLAN.md           # Phased project roadmap
```
