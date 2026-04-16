# Mutell API Manual

> **Version**: 0.1.0  
> **Base URL**: `http://localhost:8000`  
> **API Prefix**: `/api/v1`  
> **Date**: April 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication](#2-authentication)
3. [Role-Based Access Control (RBAC)](#3-role-based-access-control-rbac)
4. [Common Patterns](#4-common-patterns)
5. [Auth Endpoints](#5-auth-endpoints)
6. [Slots Endpoints](#6-slots-endpoints)
7. [Evaluations Endpoints](#7-evaluations-endpoints)
8. [Aggregations Endpoints](#8-aggregations-endpoints)
9. [Terminals Endpoints](#9-terminals-endpoints)
10. [Users Endpoints](#10-users-endpoints)
11. [Tenants Endpoints](#11-tenants-endpoints)
12. [Notes Endpoints](#12-notes-endpoints)
13. [Reports Endpoints](#13-reports-endpoints)
14. [Plans Endpoints](#14-plans-endpoints)
15. [AI Settings Endpoints](#15-ai-settings-endpoints)
16. [Admin Endpoints](#16-admin-endpoints)
17. [Dashboard Endpoints](#17-dashboard-endpoints)
18. [Schemas Reference](#18-schemas-reference)
19. [Error Codes](#19-error-codes)
20. [Seed Credentials](#20-seed-credentials)

---

## 1. Overview

Mutell is a multi-tenant SaaS platform for monitoring and evaluating POS terminal interactions. Terminals upload interaction transcripts (called **slots**), AI providers evaluate them across 8 quality metrics, and users view results via dashboards and reports.

### Architecture

- **Backend**: FastAPI (async) + SQLAlchemy 2.0 + PostgreSQL + Redis + Celery
- **Frontend**: Next.js portal (port 3000)
- **Task Queue**: Celery workers process slot evaluation and report generation asynchronously

### Key Concepts

| Concept | Description |
|---|---|
| **Tenant** | An organization using the platform. Each tenant has its own data scope. |
| **Terminal** | A POS device that uploads interaction transcripts via API key auth. |
| **Slot** | A single interaction transcript with start/end times, raw text, and AI evaluation results. |
| **Evaluation** | AI-generated quality assessment of a slot across 8 metrics (sentiment, politeness, compliance, resolution, upselling, response_time, honesty, overall). |
| **Aggregation** | Pre-computed score averages for a tenant over time periods (day, week, month). |
| **Report** | Exported PDF/CSV report of evaluation data for a time range. |

### Slot Lifecycle

```
accepted → pending → processing → evaluated
                                → unclear
                                → failed
```

- **accepted**: Slot uploaded by terminal, awaiting evaluation
- **pending**: Queued for AI evaluation
- **processing**: Currently being evaluated by AI
- **evaluated**: Evaluation complete with scores
- **unclear**: AI could not evaluate (flagged as unclear)
- **failed**: Evaluation error

### Report Lifecycle

```
generating → ready → (deleted)
```

### Health Check

```
GET /health
```

No authentication required. Returns `{"status": "ok"}`.

---

## 2. Authentication

There are two authentication methods depending on the actor:

### 2.1 User Authentication (JWT Bearer Token)

Used by all frontend-initiated requests. Users log in with email/password and receive access + refresh tokens.

**Login flow**:
1. `POST /api/v1/auth/login` with `{email, password}` → receive `access_token` and `refresh_token`
2. Include `Authorization: Bearer <access_token>` in all subsequent requests
3. When access token expires (15 min), call `POST /api/v1/auth/refresh` with the refresh token
4. Refresh tokens expire after 7 days

**Token payload** (access):
```json
{
  "sub": "<user-uuid>",
  "role": "<role>",
  "tenant_id": "<tenant-uuid or null>",
  "exp": 1234567890,
  "type": "access"
}
```

**Token payload** (refresh):
```json
{
  "sub": "<user-uuid>",
  "exp": 1234567890,
  "type": "refresh"
}
```

**Algorithm**: HS256

**Logout**: Adds user ID to Redis blacklist. Blacklisted tokens are rejected even if not expired.

### 2.2 Terminal Authentication (API Key)

Used by POS terminals uploading slots. Terminals authenticate with a generated API key.

**API key format**: `pk_live_<32-char-random-token>`

**Usage**: `Authorization: Bearer pk_live_<token>`

**Key lifecycle**:
- Generated when a terminal is created (shown only once)
- Verified via bcrypt hash comparison
- `last_seen_at` is updated on each successful authentication

### 2.3 Headers

All authenticated requests require:

```
Authorization: Bearer <token>
```

Responses include:

```
X-Request-ID: <8-char-uuid>
```

---

## 3. Role-Based Access Control (RBAC)

### Role Hierarchy

| Role | Level | Description |
|---|---|---|
| `super_admin` | 4 | Platform-wide administrator. Access to all tenants and admin endpoints. No tenant scope. |
| `tenant_admin` | 3 | Organization administrator. Full access within their tenant. |
| `manager` | 2 | Can manage users and view reports within their tenant. |
| `viewer` | 1 | Read-only access. Cannot create notes, reports, or manage users. |

### Role Enforcement Rules

1. **Privilege escalation prevention**: A user cannot invite or promote another user to a role with a higher level than their own. For example, a `manager` (level 2) cannot create a `tenant_admin` (level 3).
2. **Self-deletion prevention**: Users cannot delete their own account.
3. **Tenant scoping**: All non-super_admin users are scoped to their own `tenant_id`. They cannot access data from other tenants.
4. **Viewer restrictions**: Viewers cannot create notes or generate reports.
5. **Admin-only endpoints**: Terminal management, user invitation/deletion, and AI configuration require `super_admin` or `tenant_admin` role.

### Quick Reference: Endpoint Access Matrix

| Endpoint Group | super_admin | tenant_admin | manager | viewer |
|---|---|---|---|---|
| Auth (login, refresh, etc.) | Y | Y | Y | Y |
| Slots (list, detail) | Y | Y | Y | Y |
| Slots (create) | - | - | - | - (terminal only) |
| Slots (re-evaluate, bulk) | Y | Y | - | - |
| Evaluations | Y | Y | Y | Y |
| Aggregations | Y | Y | Y | Y |
| Terminals (CRUD, ping) | Y | Y | - | - |
| Users (list) | Y | Y | Y | - |
| Users (invite) | Y | Y | Y | - |
| Users (delete, permissions) | Y | Y | - | - |
| Tenants (list, detail) | Y | Y | Y | Y |
| Tenants (create, delete) | Y | - | - | - |
| Tenants (update) | Y | Y (own only) | - | - |
| Notes (list) | Y | Y | Y | Y |
| Notes (create) | Y | Y | Y | - |
| Notes (edit, delete own) | Y | Y | Y | Y |
| Notes (edit, delete any) | Y | Y | - | - |
| Reports (list, download) | Y | Y | Y | Y |
| Reports (create) | Y | Y | Y | - |
| Reports (delete) | Y | Y | Y | - |
| Plans (list, detail) | Y | Y | Y | Y |
| Plans (create, update) | Y | - | - | - |
| AI Settings | Y | Y | - | - |
| Admin (all) | Y | - | - | - |
| Dashboard | Y | Y | Y | Y |

---

## 4. Common Patterns

### Pagination

List endpoints use query parameters:

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `page` | int | 1 | ge 1 |
| `per_page` | int | 20 | ge 1, le 100 |

**Paginated response format**:

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "per_page": 20
}
```

### Date Format

All dates use **ISO 8601** format: `2026-04-15T10:30:00Z` or `2026-04-15T10:30:00+00:00`.

### UUID Format

All IDs are UUIDs in string format: `550e8400-e29b-41d4-a716-446655440000`.

### Error Response Format

```json
{
  "detail": "Error message string"
}
```

Or for validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```

### Success Response Format

```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
}
```

### Tenant Scoping

Most endpoints automatically filter by the authenticated user's `tenant_id`. If a user has no tenant assigned, they receive a `400 "User has no tenant"` error. Super admins are exempt from tenant scoping on admin endpoints.

### HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async processing) |
| 204 | No Content (successful deletion) |
| 400 | Bad Request |
| 401 | Unauthorized (missing/invalid token) |
| 402 | Payment Required (plan limit exceeded) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate resource) |
| 422 | Validation Error |

---

## 5. Auth Endpoints

### `POST /api/v1/auth/login`

Authenticate a user and receive tokens.

**Auth**: None (public)

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "tenant_admin",
    "tenant_id": "uuid"
  }
}
```

**Errors**:
- `401` — `{"detail": "Invalid email or password"}`

---

### `POST /api/v1/auth/refresh`

Refresh an expired access token using a refresh token.

**Auth**: None (uses refresh token in body)

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOi..."
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

**Errors**:
- `401` — `{"detail": "Invalid or expired refresh token"}`

---

### `POST /api/v1/auth/logout`

Blacklist the current access token.

**Auth**: User JWT (any authenticated user)

**Request Body**: None

**Response** (200):
```json
{
  "success": true,
  "message": "Logged out"
}
```

---

### `POST /api/v1/auth/forgot-password`

Request a password reset email. Always returns success to prevent email enumeration.

**Auth**: None (public)

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "If the email exists, a reset link has been sent"
}
```

---

### `POST /api/v1/auth/reset-password`

Reset password using a token received via email.

**Auth**: None (public)

**Request Body**:
```json
{
  "token": "reset-token-string",
  "new_password": "min-8-chars"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Password has been reset"
}
```

**Errors**:
- `400` — `{"detail": "Invalid or expired reset token"}`

---

### `POST /api/v1/auth/accept-invite`

Accept an invitation and set up the user account.

**Auth**: None (public)

**Request Body**:
```json
{
  "token": "invite-token-string",
  "full_name": "Jane Smith",
  "password": "min-8-chars"
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "jane@company.com",
    "full_name": "Jane Smith",
    "role": "manager",
    "tenant_id": "uuid"
  }
}
```

**Errors**:
- `400` — `{"detail": "Invalid or expired invitation"}`

---

### `GET /api/v1/auth/me`

Get the current authenticated user's profile.

**Auth**: User JWT (any authenticated user)

**Response** (200):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "tenant_admin",
  "tenant_id": "uuid"
}
```

---

### `POST /api/v1/auth/change-password`

Change the current user's password.

**Auth**: User JWT (any authenticated user)

**Request Body**:
```json
{
  "current_password": "old-password",
  "new_password": "min-8-chars"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Errors**:
- `400` — `{"detail": "Current password is incorrect"}`

---

### `POST /api/v1/auth/register`

Register a new user. If `tenant_slug` is provided, the user joins that tenant as a `viewer`. If omitted, a new tenant is created and the user becomes its `tenant_admin`.

**Auth**: None (public)

**Request Body**:
```json
{
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "password": "min-8-chars",
  "tenant_slug": "optional-existing-tenant"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string (email) | Yes | Unique email address |
| `full_name` | string | Yes | Full display name |
| `password` | string | Yes | Minimum 8 characters |
| `tenant_slug` | string | No | Join existing tenant; omit to create new |

**Response** (200):
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "Jane Smith",
    "role": "tenant_admin",
    "tenant_id": "uuid"
  }
}
```

**Errors**:
- `400` — `{"detail": "Email already registered or tenant not found"}`
- `422` — Validation error (password < 8 chars, missing fields)

---

### `POST /api/v1/auth/google`

Authenticate via Google OAuth. Exchange a Google ID token (obtained from the Google Sign-In client library) for a Mutell JWT. If no user exists for the Google email, a new tenant and admin user are created automatically.

**Auth**: None (public)

**Request Body**:
```json
{
  "id_token": "google-id-token-from-client-library"
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@gmail.com",
    "full_name": "Jane Smith",
    "role": "tenant_admin",
    "tenant_id": "uuid"
  }
}
```

**Errors**:
- `401` — `{"detail": "Google authentication failed"}`

**Notes**:
- Requires `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in environment config.
- If a user with the Google email already exists, they are logged in (no new tenant created).

---

## 6. Slots Endpoints

### `POST /api/v1/slots`

Upload a new interaction transcript. Called by terminals using API key auth.

**Auth**: Terminal API key (`Bearer pk_live_...`)

**Request Body**:
```json
{
  "started_at": "2026-04-15T10:00:00Z",
  "ended_at": "2026-04-15T10:05:00Z",
  "raw_text": "Customer: I'd like to return this item...\nAgent: Of course, let me help you...",
  "metadata": {
    "terminal_version": "2.1.0",
    "branch_id": "BR-0042"
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `started_at` | datetime (ISO 8601) | Yes | Interaction start time |
| `ended_at` | datetime (ISO 8601) | Yes | Interaction end time |
| `raw_text` | string | Yes | Max 100,000 characters |
| `metadata` | object | No | Key-value pairs (str/int/float/bool values) |

**Response** (202):
```json
{
  "slot_id": "uuid",
  "status": "accepted",
  "config": {
    "slot_duration_secs": 300
  }
}
```

**Errors**:
- `402` — `{"detail": "Daily slot quota exceeded"}`

**cURL**:
```bash
curl -X POST http://localhost:8000/api/v1/slots \
  -H "Authorization: Bearer pk_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"started_at":"2026-04-15T10:00:00Z","ended_at":"2026-04-15T10:05:00Z","raw_text":"Customer transcript..."}'
```

---

### `GET /api/v1/slots`

List slots for the current user's tenant with filtering and pagination.

**Auth**: User JWT (any authenticated user)

**Query Parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number (ge 1) |
| `per_page` | int | 20 | Items per page (ge 1, le 100) |
| `terminal_id` | UUID | - | Filter by terminal |
| `status` | string | - | Filter by slot status (pending, processing, evaluated, unclear, failed) |
| `date_from` | ISO 8601 | - | Filter slots starting from this date |
| `date_to` | ISO 8601 | - | Filter slots ending before this date |
| `min_score` | float | - | Minimum evaluation overall score (ge 0, le 100) |
| `max_score` | float | - | Maximum evaluation overall score (ge 0, le 100) |

**Response** (200):
```json
{
  "items": [
    {
      "id": "uuid",
      "terminal_id": "uuid",
      "tenant_id": "uuid",
      "started_at": "2026-04-15T10:00:00Z",
      "ended_at": "2026-04-15T10:05:00Z",
      "duration_secs": 300,
      "language": "en",
      "word_count": 245,
      "status": "evaluated",
      "metadata": {},
      "created_at": "2026-04-15T10:05:30Z"
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 20
}
```

**Errors**:
- `400` — `{"detail": "User has no tenant"}`
- `400` — `{"detail": "Invalid date_from: <value>"}` or `{"detail": "Invalid date_to: <value>"}`

**cURL**:
```bash
curl http://localhost:8000/api/v1/slots?page=1&per_page=10&status=evaluated&min_score=70 \
  -H "Authorization: Bearer <access_token>"
```

---

### `GET /api/v1/slots/{slot_id}`

Get full details of a single slot including raw text and evaluation.

**Auth**: User JWT (any authenticated user)

**Path Parameters**: `slot_id` (UUID)

**Response** (200):
```json
{
  "id": "uuid",
  "terminal_id": "uuid",
  "tenant_id": "uuid",
  "started_at": "2026-04-15T10:00:00Z",
  "ended_at": "2026-04-15T10:05:00Z",
  "duration_secs": 300,
  "language": "en",
  "word_count": 245,
  "status": "evaluated",
  "metadata": {},
  "created_at": "2026-04-15T10:05:30Z",
  "raw_text": "Customer: I'd like to return this item...\nAgent: Of course...",
  "evaluation": {
    "id": "uuid",
    "slot_id": "uuid",
    "tenant_id": "uuid",
    "ai_provider": "openai",
    "ai_model": "gpt-4",
    "prompt_version": "v2.1",
    "score_overall": 85.5,
    "score_sentiment": 90.0,
    "score_politeness": 88.0,
    "score_compliance": 92.0,
    "score_resolution": 80.0,
    "score_upselling": 70.0,
    "score_response_time": 95.0,
    "score_honesty": 85.0,
    "sentiment_label": "positive",
    "language_detected": "en",
    "summary": "The agent handled the return request professionally...",
    "strengths": ["Polite greeting", "Clear explanation of return policy"],
    "weaknesses": ["Missed opportunity to suggest exchange"],
    "recommendations": ["Offer exchange options proactively"],
    "unclear_items": null,
    "flags": null,
    "tokens_used": 1250,
    "evaluation_duration_ms": 3200,
    "is_unclear": false,
    "created_at": "2026-04-15T10:06:00Z"
  }
}
```

**Errors**:
- `400` — `{"detail": "User has no tenant"}`
- `404` — `{"detail": "Slot not found"}`

---

### `POST /api/v1/slots/{slot_id}/re-evaluate`

Trigger re-evaluation of a slot by AI.

**Auth**: User JWT (`super_admin` or `tenant_admin` only)

**Path Parameters**: `slot_id` (UUID)

**Response** (200):
```json
{
  "slot_id": "uuid",
  "status": "re-evaluating"
}
```

**Errors**:
- `403` — `{"detail": "Only admins can re-evaluate"}`
- `400` — `{"detail": "User has no tenant"}`
- `404` — `{"detail": "Slot not found"}`

---

### `POST /api/v1/slots/bulk-re-evaluate`

Trigger re-evaluation of multiple slots at once (max 100).

**Auth**: User JWT (`super_admin` or `tenant_admin` only)

**Request Body**:
```json
{
  "slot_ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `slot_ids` | list[string] | Yes | Max 100 UUIDs |

**Response** (200):
```json
{
  "queued": 3,
  "slot_ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

**Errors**:
- `403` — `{"detail": "Only admins can re-evaluate"}`
- `400` — `{"detail": "User has no tenant"}`
- `400` — `{"detail": "No valid slot IDs provided"}`

**cURL**:
```bash
curl -X POST http://localhost:8000/api/v1/slots/bulk-re-evaluate \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"slot_ids":["uuid-1","uuid-2","uuid-3"]}'
```

---

## 7. Evaluations Endpoints

### `GET /api/v1/evaluations/{slot_id}`

Get the evaluation for a specific slot.

**Auth**: User JWT (any authenticated user)

**Path Parameters**: `slot_id` (UUID)

**Response** (200): See `evaluation` object in Slot Detail response above.

**Errors**:
- `400` — `{"detail": "User has no tenant"}`
- `404` — `{"detail": "Evaluation not found"}`

---

## 8. Aggregations Endpoints

### `GET /api/v1/aggregations`

Get pre-computed aggregated evaluation scores.

**Auth**: User JWT (any authenticated user)

**Query Parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `period_type` | string | `"day"` | Aggregation period: `day`, `week`, `month` |
| `period_start` | ISO 8601 | - | Start of period |
| `period_end` | ISO 8601 | - | End of period |
| `terminal_id` | UUID | - | Filter by terminal |

**Response** (200):
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "terminal_id": null,
      "period_type": "day",
      "period_start": "2026-04-15T00:00:00Z",
      "period_end": "2026-04-16T00:00:00Z",
      "slot_count": 42,
      "avg_overall": 82.5,
      "avg_sentiment": 85.0,
      "avg_politeness": 88.0,
      "avg_compliance": 90.0,
      "avg_resolution": 78.0,
      "avg_upselling": 65.0,
      "avg_response_time": 92.0,
      "avg_honesty": 85.0,
      "unclear_count": 2,
      "flag_counts": {},
      "computed_at": "2026-04-15T23:59:59Z"
    }
  ],
  "total": 30
}
```

**Errors**:
- `400` — `{"detail": "User has no tenant"}`
- `400` — `{"detail": "Invalid period_start/period_end format"}`

**cURL**:
```bash
curl "http://localhost:8000/api/v1/aggregations?period_type=week&period_start=2026-04-14T00:00:00Z&period_end=2026-04-20T23:59:59Z" \
  -H "Authorization: Bearer <access_token>"
```

---

## 9. Terminals Endpoints

### `GET /api/v1/terminals`

List terminals.

**Auth**: User JWT (`super_admin` or `tenant_admin`)

**Query Parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (max 100) |

**Response** (200):
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "name": "Main Counter Terminal",
      "description": "Primary checkout terminal",
      "api_key_prefix": "a1b2c3d4",
      "location": "Store #42 - Downtown",
      "status": "active",
      "last_seen_at": "2026-04-15T14:30:00Z",
      "created_at": "2026-04-01T10:00:00Z"
    }
  ],
  "total": 5
}
```

**Errors**:
- `403` — `{"detail": "Admin only"}`

---

### `POST /api/v1/terminals`

Create a new terminal and generate its API key.

**Auth**: User JWT (`super_admin` or `tenant_admin`)

**Request Body**:
```json
{
  "name": "Main Counter Terminal",
  "description": "Primary checkout terminal",
  "location": "Store #42 - Downtown"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | Yes | Terminal display name |
| `description` | string | No | Optional description |
| `location` | string | No | Physical location |

**Response** (201):
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "name": "Main Counter Terminal",
  "description": "Primary checkout terminal",
  "api_key_prefix": "a1b2c3d4",
  "api_key": "pk_live_abc123def456ghi789jkl012mno345pqr",
  "location": "Store #42 - Downtown",
  "status": "active",
  "last_seen_at": null,
  "created_at": "2026-04-15T10:00:00Z"
}
```

> **Important**: The `api_key` is returned only once at creation time. It cannot be retrieved later.

**Errors**:
- `403` — `{"detail": "Admin only"}`
- `400` — `{"detail": "User has no tenant"}`
- `402` — `{"detail": "Terminal limit reached"}`

---

### `PATCH /api/v1/terminals/{terminal_id}`

Update a terminal's metadata.

**Auth**: User JWT (`super_admin` or `tenant_admin`)

**Path Parameters**: `terminal_id` (UUID)

**Request Body** (all fields optional):
```json
{
  "name": "Updated Terminal Name",
  "description": "New description",
  "location": "New location"
}
```

**Response** (200): `TerminalResponse` (same as list item, without `api_key`)

**Errors**:
- `403` — `{"detail": "Admin only"}`
- `404` — `{"detail": "Terminal not found"}`

---

### `DELETE /api/v1/terminals/{terminal_id}`

Revoke (soft-delete) a terminal. Sets status to `"revoked"`.

**Auth**: User JWT (`super_admin` or `tenant_admin`)

**Path Parameters**: `terminal_id` (UUID)

**Response**: `204 No Content`

**Errors**:
- `403` — `{"detail": "Admin only"}`
- `404` — `{"detail": "Terminal not found"}`

---

### `POST /api/v1/terminals/{terminal_id}/ping`

Update a terminal's last seen timestamp (heartbeat).

**Auth**: User JWT (`super_admin` or `tenant_admin`)

**Path Parameters**: `terminal_id` (UUID)

**Response** (200):
```json
{
  "success": true,
  "data": {
    "terminal_id": "uuid",
    "last_seen_at": "2026-04-15T14:30:00Z"
  }
}
```

**Errors**:
- `403` — `{"detail": "Admin only"}`
- `404` — `{"detail": "Terminal not found"}`

---

## 10. Users Endpoints

### `GET /api/v1/users`

List users in the current tenant.

**Auth**: User JWT (`super_admin`, `tenant_admin`, or `manager`)

**Query Parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (max 100) |

**Response** (200):
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "email": "user@company.com",
      "full_name": "Jane Smith",
      "avatar_url": null,
      "role": "manager",
      "status": "active",
      "last_login_at": "2026-04-15T09:00:00Z",
      "created_at": "2026-03-01T10:00:00Z"
    }
  ],
  "total": 8
}
```

**Errors**:
- `403` — `{"detail": "Insufficient permissions"}`

---

### `POST /api/v1/users/invite`

Invite a new user to the tenant. Sends an invitation email.

**Auth**: User JWT (`super_admin`, `tenant_admin`, or `manager`)

**Request Body**:
```json
{
  "email": "newuser@company.com",
  "full_name": "New User",
  "role": "viewer"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | email | Yes | Must not already be registered |
| `full_name` | string | Yes | |
| `role` | string | Yes | One of: `super_admin`, `tenant_admin`, `manager`, `viewer` |

**Response** (201): `UserResponse` (status will be `"invited"`)

**Errors**:
- `403` — `{"detail": "Insufficient permissions"}`
- `403` — `{"detail": "Cannot invite user with role 'super_admin' above your own role"}`
- `402` — `{"detail": "User limit reached"}`
- `409` — `{"detail": "Email already registered"}`
- `400` — `{"detail": "User has no tenant"}`

---

### `PATCH /api/v1/users/{user_id}`

Update a user's profile or role.

**Auth**: User JWT (any authenticated user)

**Path Parameters**: `user_id` (UUID)

**Request Body** (all fields optional):
```json
{
  "full_name": "Updated Name",
  "role": "manager",
  "status": "active"
}
```

| Field | Type | Notes |
|---|---|---|
| `full_name` | string | Any user can update their own name |
| `role` | string | One of: `super_admin`, `tenant_admin`, `manager`, `viewer`. Requires admin/manager role. Cannot promote above own level. |
| `status` | string | One of: `active`, `suspended`, `invited`. Requires admin role. |

**Response** (200): `UserResponse`

**Errors**:
- `403` — `{"detail": "Cannot assign role 'tenant_admin' above your own level"}`
- `404` — User not found

**Rules**:
- Any user can edit their own `full_name`
- Editing other users requires `super_admin`, `tenant_admin`, or `manager` role
- Cross-tenant access denied unless `super_admin`
- Role promotion is capped by the acting user's own role level

---

### `DELETE /api/v1/users/{user_id}`

Suspend (soft-delete) a user. Sets status to `"suspended"`.

**Auth**: User JWT (`super_admin` or `tenant_admin`)

**Path Parameters**: `user_id` (UUID)

**Response**: `204 No Content`

**Errors**:
- `403` — `{"detail": "Admin only"}`
- `400` — `{"detail": "Cannot suspend your own account"}`
- `404` — User not found
- `403` — `{"detail": "Cross-tenant access denied"}`

---

### `PUT /api/v1/users/{user_id}/permissions`

Set granular permissions for a user.

**Auth**: User JWT (`super_admin` or `tenant_admin`)

**Path Parameters**: `user_id` (UUID)

**Request Body**:
```json
[
  {"permission": "export_reports", "granted": true},
  {"permission": "view_analytics", "granted": true},
  {"permission": "manage_terminals", "granted": false}
]
```

**Response** (200):
```json
{
  "success": true
}
```

**Errors**:
- `403` — `{"detail": "Admin only"}`
- `400` — `{"detail": "User has no tenant"}`
- `404` — User not found

---

### `GET /api/v1/users/{user_id}/permissions`

Read a user's current permissions.

**Auth**: User JWT (`super_admin`, `tenant_admin`, or `manager`)

**Path Parameters**: `user_id` (UUID)

**Response** (200):
```json
{
  "user_id": "uuid",
  "permissions": [
    {"permission": "export_reports", "granted": true},
    {"permission": "view_analytics", "granted": false}
  ]
}
```

**Errors**:
- `403` — `{"detail": "Insufficient permissions"}`
- `404` — User not found

---

### `GET /api/v1/users/meta/permissions`

Get the list of available permission keys with labels and descriptions. Used by the frontend to dynamically render the permissions modal.

**Auth**: User JWT (any authenticated user)

**Response** (200):
```json
{
  "permissions": [
    {"key": "export_reports", "label": "Export Reports", "description": "Download and export report files"},
    {"key": "view_analytics", "label": "View Analytics", "description": "Access analytics dashboards"},
    {"key": "manage_terminals", "label": "Manage Terminals", "description": "Create, edit, and revoke terminals"},
    {"key": "manage_users", "label": "Manage Users", "description": "Invite, edit, and suspend users"},
    {"key": "create_notes", "label": "Create Notes", "description": "Add notes to slots"},
    {"key": "generate_reports", "label": "Generate Reports", "description": "Create new report exports"}
  ]
}
```

---

## 11. Tenants Endpoints

### `GET /api/v1/tenants`

List tenants.

**Auth**: User JWT (any authenticated user)

**Behavior**:
- `super_admin`: Returns paginated list of all tenants
- Other roles: Returns single-item list containing only their own tenant

**Query Parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (max 100) |

**Response** (200):
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Demo Corporation",
      "slug": "demo-corp",
      "logo_url": null,
      "contact_email": "admin@demo-corp.com",
      "contact_phone": "+1234567890",
      "address": "123 Main St, City",
      "timezone": "UTC",
      "status": "active",
      "plan_id": "uuid",
      "slot_duration_secs": 300,
      "created_at": "2026-03-01T10:00:00Z",
      "updated_at": "2026-04-15T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### `POST /api/v1/tenants`

Create a new tenant.

**Auth**: User JWT (`super_admin` only)

**Request Body**:
```json
{
  "name": "New Company",
  "slug": "new-company",
  "contact_email": "admin@new-company.com",
  "contact_phone": "+1234567890",
  "address": "456 Oak Ave, Town",
  "timezone": "America/New_York",
  "plan_id": "uuid",
  "slot_duration_secs": 300
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | Yes | Display name |
| `slug` | string | Yes | Unique URL slug |
| `contact_email` | email | Yes | |
| `contact_phone` | string | No | |
| `address` | string | No | |
| `timezone` | string | No | Default: `"UTC"` |
| `plan_id` | UUID | No | |
| `slot_duration_secs` | int | No | Default: `300` |

**Response** (201): `TenantResponse`

**Errors**:
- `403` — `{"detail": "Super Admin only"}`
- `409` — `{"detail": "Slug already taken"}`

---

### `GET /api/v1/tenants/{tenant_id}`

Get a single tenant's details.

**Auth**: User JWT (must own tenant or be `super_admin`)

**Path Parameters**: `tenant_id` (UUID)

**Response** (200): `TenantResponse`

**Errors**:
- `403` — Cross-tenant access denied
- `404` — Tenant not found

---

### `PATCH /api/v1/tenants/{tenant_id}`

Update a tenant.

**Auth**: User JWT (`super_admin`, or `tenant_admin` where tenant matches their own)

**Path Parameters**: `tenant_id` (UUID)

**Request Body** (all fields optional):
```json
{
  "name": "Updated Company Name",
  "contact_email": "new@company.com",
  "contact_phone": "+9876543210",
  "address": "New address",
  "timezone": "America/Chicago",
  "slot_duration_secs": 600,
  "plan_id": "uuid"
}
```

> **Note**: The `slug` field cannot be updated via this endpoint.
> **Note**: The `status` field is accepted in the request body but silently ignored by the update logic. To change a tenant's status, use the admin endpoint (`DELETE` for soft-delete).

**Response** (200): `TenantResponse`

**Errors**:
- `403` — Insufficient permissions
- `404` — Tenant not found

---

### `DELETE /api/v1/tenants/{tenant_id}`

Soft-delete a tenant. Sets status to `"deleted"`.

**Auth**: User JWT (`super_admin` only)

**Path Parameters**: `tenant_id` (UUID)

**Response**: `204 No Content`

**Errors**:
- `403` — `{"detail": "Super Admin only"}`
- `404` — Tenant not found

---

## 12. Notes Endpoints

### `GET /api/v1/notes`

List notes for the current tenant.

**Auth**: User JWT (any authenticated user)

**Query Parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `slot_id` | UUID | - | Filter by slot |
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (max 100) |

**Response** (200):
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "user_id": "uuid",
      "slot_id": "uuid",
      "content": "Agent handled this interaction well, but missed upsell opportunity.",
      "created_at": "2026-04-15T11:00:00Z",
      "updated_at": "2026-04-15T11:00:00Z"
    }
  ],
  "total": 3
}
```

**Errors**:
- `400` — `{"detail": "User has no tenant"}`

---

### `POST /api/v1/notes`

Add a note to a slot.

**Auth**: User JWT (role must NOT be `viewer`)

**Request Body**:
```json
{
  "slot_id": "uuid",
  "content": "This interaction needs review by compliance team."
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `slot_id` | UUID | Yes | Slot to attach note to |
| `content` | string | Yes | Min 1 character |

**Response** (201): `NoteResponse`

**Errors**:
- `403` — `{"detail": "Viewers cannot add notes"}`
- `400` — `{"detail": "User has no tenant"}`
- `404` — `{"detail": "Slot not found"}`

---

### `PATCH /api/v1/notes/{note_id}`

Update a note's content.

**Auth**: User JWT (any authenticated user)

**Path Parameters**: `note_id` (UUID)

**Request Body**:
```json
{
  "content": "Updated note text."
}
```

**Response** (200): `NoteResponse`

**Errors**:
- `404` — Note not found
- `403` — `{"detail": "Can only edit your own notes"}`

> `super_admin` and `tenant_admin` can edit any note regardless of author.

---

### `DELETE /api/v1/notes/{note_id}`

Delete a note (hard delete).

**Auth**: User JWT (any authenticated user)

**Path Parameters**: `note_id` (UUID)

**Response**: `204 No Content`

**Errors**:
- `404` — Note not found
- `403` — `{"detail": "Can only delete your own notes"}`

> `super_admin` and `tenant_admin` can delete any note regardless of author.

---

## 13. Reports Endpoints

### `GET /api/v1/reports`

List reports for the current tenant.

**Auth**: User JWT (any authenticated user)

**Query Parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (max 100) |

**Response** (200):
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "generated_by": "uuid",
      "title": "Weekly Quality Report",
      "period_start": "2026-04-07T00:00:00Z",
      "period_end": "2026-04-14T23:59:59Z",
      "terminal_ids": ["uuid-1", "uuid-2"],
      "file_url": "https://s3.amazonaws.com/mutell-reports/...",
      "file_size_bytes": 245000,
      "status": "ready",
      "created_at": "2026-04-15T08:00:00Z"
    }
  ],
  "total": 5
}
```

**Errors**:
- `400` — `{"detail": "User has no tenant"}`

---

### `POST /api/v1/reports`

Generate a new report. Report generation is asynchronous.

**Auth**: User JWT (role must NOT be `viewer`)

**Request Body**:
```json
{
  "title": "Weekly Quality Report",
  "period_start": "2026-04-07T00:00:00Z",
  "period_end": "2026-04-14T23:59:59Z",
  "terminal_ids": ["uuid-1", "uuid-2"],
  "include_transcripts": false,
  "include_notes": true,
  "accent_color": "#1a73e8"
}
```

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `title` | string | Yes | - | Report title |
| `period_start` | datetime | Yes | - | Report period start |
| `period_end` | datetime | Yes | - | Report period end |
| `terminal_ids` | list[UUID] | No | null | Filter by terminals |
| `include_transcripts` | bool | No | `false` | Include raw transcripts |
| `include_notes` | bool | No | `true` | Include user notes |
| `accent_color` | string | No | null | Hex color for PDF styling |

**Response** (202): `ReportResponse` (status will be `"generating"`)

**Errors**:
- `403` — `{"detail": "Viewers cannot generate reports"}`
- `400` — `{"detail": "User has no tenant"}`

> Poll `GET /api/v1/reports/{report_id}` to check when `status` becomes `"ready"`.

---

### `GET /api/v1/reports/{report_id}`

Get a single report by ID. Used to poll report status after generation.

**Auth**: User JWT (any authenticated user)

**Path Parameters**: `report_id` (UUID)

**Response** (200):
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "generated_by": "uuid",
  "title": "Weekly Quality Report",
  "period_start": "2026-04-07T00:00:00Z",
  "period_end": "2026-04-14T23:59:59Z",
  "terminal_ids": ["uuid-1", "uuid-2"],
  "file_url": "pending",
  "file_size_bytes": null,
  "status": "generating",
  "created_at": "2026-04-15T08:00:00Z"
}
```

**Errors**:
- `404` — `{"detail": "Report not found"}`
- `400` — `{"detail": "User has no tenant"}`

---

### `GET /api/v1/reports/{report_id}/download`

Get a presigned download URL for a completed report.

**Auth**: User JWT (any authenticated user)

**Path Parameters**: `report_id` (UUID)

**Response** (200):
```json
{
  "download_url": "https://s3.amazonaws.com/mutell-reports/...?X-Amz-Signature=...",
  "expires_in": 3600
}
```

**Errors**:
- `400` — `{"detail": "User has no tenant"}`
- `404` — `{"detail": "Report not found or not ready"}`

> The download URL expires after 1 hour. Request a new URL if it expires.

---

### `DELETE /api/v1/reports/{report_id}`

Delete a report and its file from S3.

**Auth**: User JWT (`super_admin`, `tenant_admin`, or `manager`)

**Path Parameters**: `report_id` (UUID)

**Response**: `204 No Content`

**Errors**:
- `403` — `{"detail": "Insufficient permissions"}`
- `400` — `{"detail": "User has no tenant"}`
- `404` — Report not found

---

## 14. Plans Endpoints

### `GET /api/v1/plans`

List plans.

**Auth**: User JWT (any authenticated user)

**Behavior**:
- `super_admin`: Lists all plans (including inactive)
- Other roles: Lists only active plans (`is_active=true`)

**Query Parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (max 100) |

**Response** (200):
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Starter",
      "description": "For small businesses",
      "max_terminals": 5,
      "max_users": 10,
      "max_slots_per_day": 1000,
      "retention_days": 90,
      "allowed_ai_providers": ["openai"],
      "custom_prompt_allowed": false,
      "report_export_allowed": true,
      "api_rate_limit_per_min": 60,
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 3
}
```

---

### `POST /api/v1/plans`

Create a new plan.

**Auth**: User JWT (`super_admin` only)

**Request Body**:
```json
{
  "name": "Enterprise",
  "description": "For large organizations",
  "max_terminals": 100,
  "max_users": 500,
  "max_slots_per_day": 50000,
  "retention_days": 365,
  "allowed_ai_providers": ["openai", "anthropic", "gemini"],
  "custom_prompt_allowed": true,
  "report_export_allowed": true,
  "api_rate_limit_per_min": 300
}
```

| Field | Type | Required | Default |
|---|---|---|---|
| `name` | string | Yes | - |
| `description` | string | No | `null` |
| `max_terminals` | int | No | `5` |
| `max_users` | int | No | `10` |
| `max_slots_per_day` | int | No | `1000` |
| `retention_days` | int | No | `90` |
| `allowed_ai_providers` | list[string] | No | `[]` |
| `custom_prompt_allowed` | bool | No | `false` |
| `report_export_allowed` | bool | No | `true` |
| `api_rate_limit_per_min` | int | No | `60` |

**Response** (201): `PlanResponse`

**Errors**:
- `403` — `{"detail": "Super Admin only"}`

---

### `GET /api/v1/plans/{plan_id}`

Get a single plan.

**Auth**: User JWT (any authenticated user)

**Path Parameters**: `plan_id` (UUID)

**Response** (200): `PlanResponse`

**Errors**:
- `404` — `{"detail": "Plan not found"}`

---

### `PATCH /api/v1/plans/{plan_id}`

Update a plan.

**Auth**: User JWT (`super_admin` only)

**Path Parameters**: `plan_id` (UUID)

**Request Body** (all fields optional):
```json
{
  "name": "Updated Plan Name",
  "max_terminals": 50,
  "is_active": false
}
```

**Response** (200): `PlanResponse`

**Errors**:
- `403` — `{"detail": "Super Admin only"}`
- `404` — `{"detail": "Plan not found"}`

---

## 15. AI Settings Endpoints

### `GET /api/v1/settings/ai`

List AI configurations for the current tenant.

**Auth**: User JWT (any authenticated user)

**Response** (200):
```json
{
  "items": [
    {
      "id": "uuid",
      "provider_id": "uuid",
      "provider_slug": "openai",
      "provider_name": "OpenAI",
      "model_id": "gpt-4",
      "is_default": true,
      "custom_prompt": null,
      "created_at": "2026-04-01T10:00:00Z"
    }
  ],
  "total": 1
}
```

**Errors**:
- `400` — `{"detail": "User has no tenant"}`

---

### `POST /api/v1/settings/ai`

Add an AI configuration for the tenant.

**Auth**: User JWT (`super_admin` or `tenant_admin`)

**Request Body**:
```json
{
  "provider_id": "uuid",
  "model_id": "gpt-4",
  "api_key": "sk-...",
  "is_default": true,
  "custom_prompt": "Evaluate this POS interaction with focus on compliance."
}
```

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `provider_id` | UUID | Yes | - | Must reference an active AI provider |
| `model_id` | string | Yes | - | Model identifier |
| `api_key` | string | Yes | - | Provider API key (encrypted at rest) |
| `is_default` | bool | No | `false` | If true, unsets previous default |
| `custom_prompt` | string | No | `null` | Custom evaluation prompt |

**Response** (201): `AIConfigResponse`

**Errors**:
- `403` — `{"detail": "Only admins can configure AI"}`
- `400` — `{"detail": "User has no tenant"}`
- `400` — `{"detail": "Provider not found or inactive"}`

---

### `PATCH /api/v1/settings/ai/{config_id}`

Update an AI configuration.

**Auth**: User JWT (`super_admin` or `tenant_admin`)

**Path Parameters**: `config_id` (UUID)

**Request Body** (all fields optional):
```json
{
  "model_id": "gpt-4-turbo",
  "api_key": "sk-new-key...",
  "is_default": true,
  "custom_prompt": "Updated prompt"
}
```

**Response** (200): `AIConfigResponse`

**Errors**:
- `403` — `{"detail": "Only admins can configure AI"}`
- `404` — `{"detail": "AI config not found"}`

---

### `DELETE /api/v1/settings/ai/{config_id}`

Delete an AI configuration.

**Auth**: User JWT (`super_admin` or `tenant_admin`)

**Path Parameters**: `config_id` (UUID)

**Response**: `204 No Content`

**Errors**:
- `403` — `{"detail": "Only admins can configure AI"}`
- `404` — `{"detail": "AI config not found"}`

---

### `GET /api/v1/settings/notifications`

Get the current user's notification preferences. Returns defaults if the user has not configured preferences yet.

**Auth**: User JWT (any authenticated user)

**Response** (200):
```json
{
  "email_evaluations": true,
  "email_failures": true,
  "email_reports": false,
  "push_mentions": true,
  "push_weekly_summary": false
}
```

---

### `PUT /api/v1/settings/notifications`

Update the current user's notification preferences. Accepts and returns the full settings object (no partial updates).

**Auth**: User JWT (any authenticated user)

**Request Body**:
```json
{
  "email_evaluations": true,
  "email_failures": false,
  "email_reports": true,
  "push_mentions": true,
  "push_weekly_summary": true
}
```

**Response** (200):
```json
{
  "email_evaluations": true,
  "email_failures": false,
  "email_reports": true,
  "push_mentions": true,
  "push_weekly_summary": true
}
```

---

## 16. Admin Endpoints

All admin endpoints require `super_admin` role.

### `GET /api/v1/admin/tenants`

List all tenants (admin view).

**Auth**: `super_admin` only

**Query Parameters**: `page`, `per_page`

**Response** (200): `TenantListResponse`

---

### `POST /api/v1/admin/tenants`

Create a tenant (admin shortcut).

**Auth**: `super_admin` only

**Request Body**: Same as `POST /api/v1/tenants`

**Response** (201): `TenantResponse`

**Errors**:
- `409` — `{"detail": "Slug already taken"}`

---

### `GET /api/v1/admin/tenants/{tenant_id}`

Get a tenant by ID.

**Auth**: `super_admin` only

**Response** (200): `TenantResponse`

**Errors**:
- `404` — Tenant not found

---

### `PATCH /api/v1/admin/tenants/{tenant_id}`

Update a tenant (admin can update any field including status).

**Auth**: `super_admin` only

**Request Body**: Same as `PATCH /api/v1/tenants` (note: `status` field is accepted but silently ignored)

**Response** (200): `TenantResponse`

**Errors**:
- `404` — Tenant not found

> **Note**: To change a tenant's status, use `DELETE /api/v1/admin/tenants/{tenant_id}` (sets status to `"deleted"`).

---

### `DELETE /api/v1/admin/tenants/{tenant_id}`

Soft-delete a tenant (sets status to `"deleted"`).

**Auth**: `super_admin` only

**Response**: `204 No Content`

**Errors**:
- `404` — Tenant not found

---

### `GET /api/v1/admin/plans`

List all plans (including inactive).

**Auth**: `super_admin` only

**Query Parameters**: `page`, `per_page`

**Response** (200): `PlanListResponse`

---

### `POST /api/v1/admin/plans`

Create a plan.

**Auth**: `super_admin` only

**Request Body**: Same as `POST /api/v1/plans`

**Response** (201): `PlanResponse`

---

### `PATCH /api/v1/admin/plans/{plan_id}`

Update a plan.

**Auth**: `super_admin` only

**Request Body**: Same as `PATCH /api/v1/plans`

**Response** (200): `PlanResponse`

**Errors**:
- `404` — Plan not found

---

### `GET /api/v1/admin/ai-providers`

List all AI providers (platform-level).

**Auth**: `super_admin` only

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "slug": "openai",
      "display_name": "OpenAI",
      "is_active": true,
      "api_key": "sk-s...5678",
      "supported_models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
    }
  ]
}
```

---

### `PATCH /api/v1/admin/ai-providers/{provider_id}`

Update an AI provider (display name, active status, API key).

**Auth**: `super_admin` only

**Path Parameters**: `provider_id` (UUID)

**Request Body** (all fields optional):
```json
{
  "display_name": "OpenAI (GPT)",
  "is_active": true,
  "api_key": "sk-..."
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `display_name` | string | No | Display name |
| `is_active` | bool | No | Toggle provider availability |
| `api_key` | string | No | Platform-level API key (masked in responses) |

**Response** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "slug": "openai",
    "display_name": "OpenAI (GPT)",
    "is_active": true,
    "api_key": "sk-s...5678",
    "supported_models": ["gpt-4", "gpt-4-turbo"]
  }
}
```

> `api_key` is masked in all responses (first 4 + last 4 chars). Tenants can override with their own key via `POST /settings/ai`.

**Errors**:
- `404` — Provider not found

---

### `POST /api/v1/admin/ai-providers/{provider_id}/models`

Add a model to an AI provider's `supported_models` list.

**Auth**: `super_admin` only

**Path Parameters**: `provider_id` (UUID)

**Request Body**:
```json
{
  "model_id": "gpt-4-turbo"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "slug": "openai",
    "display_name": "OpenAI (GPT)",
    "supported_models": ["gpt-4", "gpt-4-turbo"]
  }
}
```

**Errors**:
- `404` — Provider not found

> Adding a duplicate model is a no-op (returns 200 with unchanged list).

---

### `DELETE /api/v1/admin/ai-providers/{provider_id}/models/{model_id}`

Remove a model from an AI provider's `supported_models` list.

**Auth**: `super_admin` only

**Path Parameters**: `provider_id` (UUID), `model_id` (string, URL path)

**Response** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "slug": "openai",
    "display_name": "OpenAI (GPT)",
    "supported_models": ["gpt-4"]
  }
}
```

**Errors**:
- `404` — Provider not found

---

### `GET /api/v1/admin/users`

List all users across all tenants.

**Auth**: `super_admin` only

**Query Parameters**: `page`, `per_page`

**Response** (200): `UserListResponse`

---

### `GET /api/v1/admin/audit-log`

View the platform audit log.

**Auth**: `super_admin` only

**Query Parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `per_page` | int | 50 | Items per page (max 200) |
| `action` | string | - | Filter by action (case-insensitive partial match) |
| `date_from` | ISO 8601 | - | Filter from date |
| `date_to` | ISO 8601 | - | Filter to date |

**Response** (200):
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "user_id": "uuid",
      "action": "user.login",
      "resource_type": "user",
      "resource_id": "uuid",
      "detail": {},
      "ip_address": "192.168.1.1",
      "status_code": 200,
      "created_at": "2026-04-15T10:00:00Z"
    }
  ],
  "total": 1500,
  "page": 1,
  "per_page": 50
}
```

**Errors**:
- `400` — `{"detail": "Invalid date_from: <value>"}` or `{"detail": "Invalid date_to: <value>"}`

---

### `GET /api/v1/admin/health`

Check system health (database and Redis connectivity).

**Auth**: `super_admin` only

**Response** (200):
```json
{
  "success": true,
  "data": {
    "database": "connected",
    "redis": "connected",
    "workers": "unknown"
  }
}
```

---

## 17. Dashboard Endpoints

### `GET /api/v1/dashboard/stats`

Get tenant-scoped KPI statistics for the dashboard.

**Auth**: User JWT (any authenticated user with a tenant)

**Response** (200):
```json
{
  "success": true,
  "data": {
    "slots_today": 42,
    "slots_week": 285,
    "evaluated_today": 38,
    "failed_today": 2,
    "pending_evaluations": 5,
    "active_terminals": 8,
    "avg_score_week": 82.3,
    "avg_score_month": 80.1
  }
}
```

| Field | Type | Description |
|---|---|---|
| `slots_today` | int | Slots created today |
| `slots_week` | int | Slots created since Monday 00:00 |
| `evaluated_today` | int | Slots with status `evaluated` or `unclear` today |
| `failed_today` | int | Slots with status `failed` today |
| `pending_evaluations` | int | Slots with status `pending` or `processing` |
| `active_terminals` | int | Terminals with status `active` |
| `avg_score_week` | float or null | Average `score_overall` this week (1 decimal) |
| `avg_score_month` | float or null | Average `score_overall` since 1st of month (1 decimal) |

**Errors**:
- `400` — `{"detail": "User has no tenant"}`

**cURL**:
```bash
curl http://localhost:8000/api/v1/dashboard/stats \
  -H "Authorization: Bearer <access_token>"
```

---

### `GET /api/v1/dashboard/trends`

Get historical trend data for charts (slot counts and average scores per day).

**Auth**: User JWT (any authenticated user with a tenant)

**Query Parameters**:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `days` | int | 14 | Number of days to look back (1-90) |

**Response** (200):
```json
{
  "items": [
    { "date": "2026-04-01", "avg_score": 82.3, "slot_count": 42 },
    { "date": "2026-04-02", "avg_score": 85.1, "slot_count": 38 }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `date` | string (ISO date) | Date of data point |
| `avg_score` | float or null | Average overall score for that day |
| `slot_count` | int | Number of slots created that day |

**Errors**:
- `400` — `{"detail": "User has no tenant"}`

---

## 18. Schemas Reference

### Evaluation Metrics

All score fields are `float | null` on a 0-100 scale:

| Metric | Field | Description |
|---|---|---|
| Overall | `score_overall` | Composite quality score |
| Sentiment | `score_sentiment` | Customer sentiment quality |
| Politeness | `score_politeness` | Agent politeness and professionalism |
| Compliance | `score_compliance` | Adherence to policies and regulations |
| Resolution | `score_resolution` | Issue resolution effectiveness |
| Upselling | `score_upselling` | Cross-sell and upselling effectiveness |
| Response Time | `score_response_time` | Speed and efficiency of response |
| Honesty | `score_honesty` | Accuracy and transparency |

### User Status Values

| Status | Description |
|---|---|
| `active` | User can log in and perform actions |
| `suspended` | User account is suspended (soft-deleted) |
| `invited` | User has been invited but hasn't accepted yet |

### Slot Status Values

| Status | Description |
|---|---|
| `pending` | Awaiting evaluation |
| `processing` | Currently being evaluated |
| `evaluated` | Evaluation complete |
| `unclear` | AI could not evaluate |
| `failed` | Evaluation error |

> **Note**: `POST /api/v1/slots` returns `"status": "accepted"` in the immediate response before the slot transitions to `pending`. The `accepted` status is response-only and is not stored in the database.

### Report Status Values

| Status | Description |
|---|---|
| `generating` | Report is being generated (async) |
| `ready` | Report is ready for download |
| `failed` | Report generation failed |

### Terminal Status Values

| Status | Description |
|---|---|
| `active` | Terminal is active and can upload slots |
| `revoked` | Terminal has been revoked (soft-deleted) |

---

## 19. Error Codes

### HTTP 401 — Unauthorized

```json
{"detail": "Could not validate credentials"}
{"detail": "Invalid or expired refresh token"}
{"detail": "Invalid email or password"}
```

### HTTP 402 — Plan Limit Exceeded

```json
{"detail": "Daily slot quota exceeded"}
{"detail": "Terminal limit reached"}
{"detail": "User limit reached"}
```

### HTTP 403 — Forbidden

```json
{"detail": "Role 'viewer' not permitted. Required: super_admin, tenant_admin"}
{"detail": "Super Admin only"}
{"detail": "Admin only"}
{"detail": "Insufficient permissions"}
{"detail": "Only admins can re-evaluate"}
{"detail": "Only admins can configure AI"}
{"detail": "Cannot invite user with role 'X' above your own role"}
{"detail": "Cannot assign role 'X' above your own level"}
{"detail": "Cannot suspend your own account"}
{"detail": "Cross-tenant access denied"}
{"detail": "Viewers cannot add notes"}
{"detail": "Viewers cannot generate reports"}
{"detail": "Can only edit your own notes"}
{"detail": "Can only delete your own notes"}
```

### HTTP 404 — Not Found

```json
{"detail": "Slot not found"}
{"detail": "Evaluation not found"}
{"detail": "Terminal not found"}
{"detail": "User not found"}
{"detail": "Tenant not found"}
{"detail": "Plan not found"}
{"detail": "Report not found or not ready"}
{"detail": "AI config not found"}
```

### HTTP 409 — Conflict

```json
{"detail": "Email already registered"}
{"detail": "Slug already taken"}
```

### HTTP 422 — Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 20. Seed Credentials

### Super Admin

```
Email:    admin@platform.com
Password: admin123
Role:     super_admin
Tenant:   (none — platform-level)
```

### Tenant Admin (Demo Corp)

```
Email:    admin@demo-corp.com
Password: demo123
Role:     tenant_admin
Tenant:   Demo Corporation (slug: demo-corp)
```

### Viewer (Demo Corp)

```
Email:    user@demo-corp.com
Password: demo123
Role:     viewer
Tenant:   Demo Corporation (slug: demo-corp)
```

---

## Quick Start: cURL Examples

### Login as Tenant Admin

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo-corp.com","password":"demo123"}'
```

### Get Dashboard Stats

```bash
TOKEN="<access_token from login>"
curl http://localhost:8000/api/v1/dashboard/stats \
  -H "Authorization: Bearer $TOKEN"
```

### List Slots with Score Filter

```bash
curl "http://localhost:8000/api/v1/slots?page=1&per_page=10&min_score=70&max_score=100" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Slot Detail with Evaluation

```bash
SLOT_ID="<slot-uuid>"
curl http://localhost:8000/api/v1/slots/$SLOT_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Upload Slot (Terminal)

```bash
API_KEY="<pk_live_...>"
curl -X POST http://localhost:8000/api/v1/slots \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"started_at":"2026-04-15T10:00:00Z","ended_at":"2026-04-15T10:05:00Z","raw_text":"Customer: Hello\nAgent: Hi, how can I help?"}'
```

### Invite a User

```bash
curl -X POST http://localhost:8000/api/v1/users/invite \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"new@demo-corp.com","full_name":"New User","role":"manager"}'
```

### Generate a Report

```bash
curl -X POST http://localhost:8000/api/v1/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Weekly Report","period_start":"2026-04-07T00:00:00Z","period_end":"2026-04-14T23:59:59Z"}'
```
