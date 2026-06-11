# API Specification

Base URL: `http://localhost:8000`

---

## Auth

### `POST /auth/register`

Create a new user account.

**Auth:** None

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secret123"
}
```

**Response `201`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors:** `400` — email already exists

---

### `POST /auth/login`

Authenticate and receive a JWT.

**Auth:** None

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secret123"
}
```

**Response `200`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors:** `401` — invalid email or password

---

## Service Requests (User)

All endpoints in this section require `Authorization: Bearer <token>`.

### `POST /requests`

Create a new service request.

**Request:**
```json
{
  "resource_id": "uuid-or-null",
  "title": "Need a meeting room",
  "description": "For team standup at 10am"
}
```

**Response `201`:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "resource_id": "uuid-or-null",
  "title": "Need a meeting room",
  "description": "For team standup at 10am",
  "status": "pending",
  "admin_note": null,
  "created_at": "2026-06-11T12:00:00Z",
  "updated_at": "2026-06-11T12:00:00Z"
}
```

---

### `GET /requests/me`

List all requests belonging to the authenticated user.

**Response `200`:**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "resource_id": null,
    "title": "Need a meeting room",
    "description": null,
    "status": "pending",
    "admin_note": null,
    "created_at": "2026-06-11T12:00:00Z",
    "updated_at": "2026-06-11T12:00:00Z"
  }
]
```

---

### `GET /requests/{id}`

Get a single request by ID (must be owner).

**Response `200`:** Single request object (same shape as above)

**Errors:** `404` — not found or not owned by user

---

## Admin

All endpoints in this section require `Authorization: Bearer <token>` where the user has role `admin`.

### `GET /admin/requests?status=pending`

List all service requests, optionally filtered by status.

**Query params:** `status` — one of `pending`, `approved`, `rejected`, `cancelled`

**Response `200`:** Array of request objects (same shape as above)

---

### `PATCH /admin/requests/{id}/status`

Update the status of a service request.

**Request:**
```json
{
  "status": "approved",
  "admin_note": "Resource confirmed"
}
```

`status` must be one of: `pending`, `approved`, `rejected`, `cancelled`

**Response `200`:** Updated request object

**Errors:** `404` — request not found

---

### `GET /admin/resources`

List all resources.

**Response `200`:**
```json
[
  {
    "id": "uuid",
    "name": "Meeting Room A",
    "type": "room",
    "description": "Capacity 10 people",
    "is_active": true,
    "created_at": "2026-06-11T12:00:00Z"
  }
]
```

---

### `POST /admin/resources`

Create a new resource.

**Request:**
```json
{
  "name": "Meeting Room A",
  "type": "room",
  "description": "Capacity 10 people"
}
```

`type` must be `room` or `vehicle`.

**Response `201`:** Created resource object

---

### `PATCH /admin/resources/{id}`

Update a resource.

**Request:** All fields optional.
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "is_active": false
}
```

**Response `200`:** Updated resource object

**Errors:** `404` — resource not found
