# API Specification

Base URL: `http://localhost:8001`

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

### `POST /auth/line`

Authenticate via LINE LIFF access token.

**Auth:** None

**Request:**
```json
{
  "access_token": "LINE_LIFF_ACCESS_TOKEN"
}
```

**Response `200`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors:**
- `401` — invalid LINE token or token not issued for this channel
- Verifies token with LINE API, fetches profile, auto-creates user if `line_user_id` not found
- Stores LINE `displayName` in `full_name` column

---

## Service Requests (User)

All endpoints in this section require `Authorization: Bearer <token>`.

### `POST /requests`

Create a new service request. If `resource_id`, `start_time`, and `end_time` are all provided, the system checks for time conflicts with existing approved/pending requests for the same resource.

**Request:**
```json
{
  "resource_id": "uuid-or-null",
  "title": "Need a meeting room",
  "description": "For team standup at 10am",
  "start_time": "2026-06-12T09:00:00Z",
  "end_time": "2026-06-12T10:00:00Z"
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
  "start_time": "2026-06-12T09:00:00Z",
  "end_time": "2026-06-12T10:00:00Z",
  "created_at": "2026-06-11T12:00:00Z",
  "updated_at": "2026-06-11T12:00:00Z"
}
```

**Errors:** `409` — resource time slot conflict

---

### `GET /requests/me`

List the authenticated user's requests, with pagination.

**Query params:**
- `skip` — number of records to skip (default `0`)
- `limit` — max records to return (default `20`, max `100`)

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
    "start_time": null,
    "end_time": null,
    "created_at": "2026-06-11T12:00:00Z",
    "updated_at": "2026-06-11T12:00:00Z"
  }
]
```

---

### `PATCH /requests/{id}/cancel`

Cancel the user's own pending request.

**Auth:** User must own the request.

**Response `200`:** Updated request object with `status: "cancelled"`

**Errors:**
- `404` — request not found or not owned by user
- `400` — request status is not "pending"

---

### `GET /requests/{id}`

Get a single request by ID (must be owner).

**Response `200`:** Single request object (same shape as above)

**Errors:** `404` — not found or not owned by user

---

## Admin

All endpoints in this section require `Authorization: Bearer <token>` where the user has role `admin`.

### `GET /admin/requests`

List all service requests, with optional status filter and pagination.

**Query params:**
- `status` — one of `pending`, `approved`, `rejected`, `cancelled`
- `skip` — number of records to skip (default `0`)
- `limit` — max records to return (default `20`, max `100`)

**Response `200`:** Array of request objects (same shape as above)

---

### `PATCH /admin/requests/{id}/status`

Update the status of a service request. Enforces valid transitions:

| Current Status | Allowed New Statuses |
|----------------|---------------------|
| pending | approved, rejected |
| approved | cancelled |
| rejected | (none) |
| cancelled | (none) |

**Request:**
```json
{
  "status": "approved",
  "admin_note": "Resource confirmed"
}
```

**Response `200`:** Updated request object

**Note:** On success, a fire-and-forget POST is sent to the n8n webhook with `{"request_id", "status", "admin_note"}`.

**Errors:**
- `404` — request not found
- `400` — invalid status transition

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

---

## Attachments

All endpoints in this section require `Authorization: Bearer <token>`. Files are uploaded to MinIO via S3-compatible API.

### `POST /requests/{id}/attachments`

Upload a file attachment to a service request. The user must own the request.

**Request:** Multipart form with field `file`.

Allowed content types: `image/jpeg`, `image/png`, `image/gif`, `application/pdf`. Max file size: 5MB.

**Response `201`:**
```json
{
  "id": "uuid",
  "request_id": "uuid",
  "file_url": "http://localhost:9000/admin-portal/attachments/uuid.jpg",
  "filename": "photo.jpg",
  "uploaded_by": "uuid",
  "created_at": "2026-06-11T12:00:00Z"
}
```

**Errors:**
- `404` — request not found or not owned by user
- `400` — invalid file type or file exceeds 5MB

---

### `GET /requests/{id}/attachments`

List all attachments for a service request. The user must own the request.

**Response `200`:**
```json
[
  {
    "id": "uuid",
    "request_id": "uuid",
    "file_url": "http://localhost:9000/admin-portal/attachments/uuid.jpg",
    "filename": "photo.jpg",
    "uploaded_by": "uuid",
    "created_at": "2026-06-11T12:00:00Z"
  }
]
```

**Errors:** `404` — request not found or not owned by user
