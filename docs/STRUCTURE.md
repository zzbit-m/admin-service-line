# Project Structure

```
project/
├── .env                          # Environment variables (DB URL, secret key)
├── alembic.ini                   # Alembic configuration
├── requirements.txt              # Python dependencies
├── README.md                     # Setup instructions
├── alembic/
│   ├── env.py                    # Alembic env — imports all models for autogenerate
│   ├── script.py.mako            # Migration template
│   └── versions/                 # Generated migration files
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app, CORS, lifespan, router registration
│   ├── core/
│   │   ├── config.py             # Pydantic Settings loaded from .env
│   │   ├── security.py           # bcrypt hashing + JWT create/decode
│   │   └── dependencies.py       # get_current_user / require_admin dependencies
│   ├── db/
│   │   ├── base.py               # SQLAlchemy DeclarativeBase
│   │   └── session.py            # Async engine, session maker, get_db generator
│   ├── models/
│   │   ├── user.py               # User model (id, email, hashed_password, role, line_user_id, is_active)
│   │   ├── resource.py           # Resource model (id, name, type, description, is_active)
│   │   └── request.py            # ServiceRequest model (id, user_id, resource_id, title, status, admin_note)
│   ├── schemas/
│   │   ├── auth.py               # RegisterRequest, LoginRequest, AuthResponse
│   │   ├── resource.py           # ResourceCreate/Update/Response (with Literal type validation)
│   │   └── request.py            # RequestCreate, StatusUpdate (with Literal), RequestResponse
│   ├── routers/
│   │   ├── auth.py               # POST /auth/register, /auth/login
│   │   ├── requests.py           # POST /requests, GET /requests/me, GET /requests/{id}
│   │   └── admin.py              # Admin-only CRUD for requests and resources
│   └── services/
│       ├── auth_service.py       # Register + login logic
│       ├── request_service.py    # User request CRUD
│       └── admin_service.py      # Admin request/resource management
└── docs/
    ├── ARCHITECTURE.md           # System flow, stack, layer responsibilities
    ├── API_SPEC.md               # All endpoints with request/response shapes
    ├── STRUCTURE.md              # This file
    └── PROJECT_PLAN.md           # Phased roadmap
```
