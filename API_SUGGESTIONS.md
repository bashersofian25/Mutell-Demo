# API Suggestions for Backend Dev

> Generated from portal frontend implementation review.
> These endpoints/features are needed by the UI but not currently in the API manual.
> Last updated: April 2026

---

## 1. User Registration (Signup)

**Current state**: No public registration endpoint exists. The portal has a signup page (`portal/src/app/(auth)/signup/page.tsx`) but can only show "coming soon" toast.

**Suggested endpoint**: `POST /api/v1/auth/register`

```json
{
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "password": "min-8-chars",
  "tenant_slug": "optional-existing-tenant"
}
```

**Notes**:
- If `tenant_slug` is provided, add user to that tenant as `viewer`.
- If omitted, create a new tenant (self-service onboarding flow).
- Consider email verification step.
- Response should match login response (return JWT + user object).

---

## 2. OAuth / Social Login (Google)

**Current state**: Login page has a "Sign in with Google" button (`portal/src/app/(auth)/login/page.tsx:99`) but no backend support. Shows "coming soon" toast.

**Suggested endpoints**:
- `POST /api/v1/auth/google` — Exchange Google ID token for Mutell JWT
- Or use standard OAuth2 flow with `GET /api/v1/auth/google/callback`

**Notes**:
- Frontend will use Google Sign-In client library to get ID token.
- Backend verifies token with Google, finds/creates user, returns JWT.
- Response format should match login response.

---

## 3. Admin AI Provider API Key Management

**Current state**: `PATCH /admin/ai-providers/{id}` only accepts `display_name` and `is_active` (API Manual §16). Admin UI has input fields for API key and base URL (`portal/src/app/(app)/admin/ai-providers/page.tsx:88-91`), but these fields are silently ignored by the backend.

**Suggested**: Add `api_key` and `base_url` fields to `PATCH /admin/ai-providers/{id}`

```json
{
  "display_name": "OpenAI (GPT)",
  "is_active": true,
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1"
}
```

**Notes**:
- This is the platform-level key. Tenants may optionally override with their own key via `POST /settings/ai`.
- `base_url` updates enable self-hosted model support.
- API key should be encrypted at rest and masked in GET responses.

---

## 4. Admin AI Provider Model Management

**Current state**: `supported_models` is read-only on the provider. Admin UI shows an input field for adding models (`portal/src/app/(app)/admin/ai-providers/page.tsx:129`), but no endpoint exists.

**Suggested**: Add model management to the admin provider endpoints:

`POST /admin/ai-providers/{id}/models`
```json
{ "model_id": "gpt-4-turbo" }
```

`DELETE /admin/ai-providers/{id}/models/{model_id}`

**Response** (both): Return updated provider object with full `supported_models` list.

---

## 5. User Permissions GET Endpoint

**Current state**: `PUT /users/{id}/permissions` exists to SET permissions, but there's no `GET /users/{id}/permissions` to READ current permissions. The permissions modal (`portal/src/app/(app)/team/page.tsx:86-92`) initializes all toggles to `true` because it can't fetch the actual state.

**Suggested**: `GET /api/v1/users/{user_id}/permissions`

**Response**:
```json
{
  "permissions": [
    { "permission": "export_reports", "granted": true },
    { "permission": "view_analytics", "granted": true },
    { "permission": "manage_terminals", "granted": false }
  ]
}
```

---

## 6. Audit Log Response Format Standardization

**Current state**: The audit log response (`GET /admin/audit-log`, API Manual §16) returns data in `ApiSuccessResponse` format with a top-level `data` array instead of the standard paginated `items` format used by every other list endpoint. It also lacks `page` and `per_page` in the body.

**Current response**:
```json
{
  "success": true,
  "data": [...],
  "total": 1500
}
```

**Suggested**: Return standard paginated response format consistent with all other list endpoints:

```json
{
  "items": [...],
  "total": 1500,
  "page": 1,
  "per_page": 20
}
```

**Notes**:
- The frontend (`portal/src/services/admin.ts:48-52`) currently reads total from the `X-Total-Count` header as a workaround. Standardizing the response eliminates this workaround.
- This is a **breaking change** — update the frontend `getTotal` method to read from the response body.

---

## 7. Dashboard Trends Endpoint

**Current state**: `/dashboard/stats` returns point-in-time KPIs. The dashboard chart needs historical data, which currently requires calling `/aggregations` separately with specific date ranges.

**Suggested**: `GET /api/v1/dashboard/trends?days=14`

```json
{
  "items": [
    { "date": "2026-04-01", "avg_score": 82.3, "slot_count": 42 },
    { "date": "2026-04-02", "avg_score": 85.1, "slot_count": 38 }
  ]
}
```

**Notes**: This is optional — the current approach of using `/aggregations` works, but a dedicated endpoint would be cleaner for dashboard use.

---

## 8. Terminal Ping — No Change Needed

**Current state**: `POST /terminals/{id}/ping` updates `last_seen_at`. The terminals page shows this as a manual action, but it's meant for automated heartbeat from the terminal itself.

**No change needed** — just documenting that the UI exposes this as a manual "Test Connection" button for admin debugging purposes.

---

## 9. Notification Settings API

**Current state**: The notification settings page (`portal/src/app/(app)/settings/notifications/page.tsx:43-54`) stores preferences in `localStorage` only. No server-side persistence. Settings don't sync across devices or survive browser clears.

**Suggested endpoints**:

`GET /api/v1/settings/notifications`
```json
{
  "email_evaluations": true,
  "email_failures": true,
  "email_reports": false,
  "push_mentions": true,
  "push_weekly_summary": false
}
```

`PUT /api/v1/settings/notifications`
```json
{
  "email_evaluations": true,
  "email_failures": false,
  "email_reports": true,
  "push_mentions": true,
  "push_weekly_summary": true
}
```

**Notes**:
- Accept and return the full settings object (no partial updates).
- Return defaults for users who haven't configured notifications yet.
- Auth: any authenticated user (user-scoped, not tenant-scoped).

---

## 10. Permissions Schema Endpoint

**Current state**: Permission keys are hardcoded in the frontend (`portal/src/app/(app)/team/page.tsx:37-44`). The current list is: `export_reports`, `view_analytics`, `manage_terminals`, `manage_users`, `create_notes`, `generate_reports`. If the backend adds or renames a permission, the UI won't reflect it.

**Suggested**: `GET /api/v1/permissions`

**Response**:
```json
{
  "permissions": [
    { "key": "export_reports", "label": "Export Reports", "description": "Download and export report files" },
    { "key": "view_analytics", "label": "View Analytics", "description": "Access analytics dashboards" },
    { "key": "manage_terminals", "label": "Manage Terminals", "description": "Create, edit, and revoke terminals" },
    { "key": "manage_users", "label": "Manage Users", "description": "Invite, edit, and suspend users" },
    { "key": "create_notes", "label": "Create Notes", "description": "Add notes to slots" },
    { "key": "generate_reports", "label": "Generate Reports", "description": "Create new report exports" }
  ]
}
```

**Notes**:
- Auth: any authenticated user (read-only metadata).
- This is a quality-of-life improvement — the frontend can dynamically render the permissions modal instead of hardcoding keys.

---

## 11. Report Detail Endpoint — Document Existing Endpoint

**Current state**: The API manual mentions *"Poll `GET /api/v1/reports/{report_id}` to check when status becomes 'ready'"* (API Manual §13), but this endpoint is never formally documented with request/response schemas.

**Suggested**: Add formal documentation for `GET /api/v1/reports/{report_id}`

**Auth**: User JWT (any authenticated user)

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
  "file_url": null,
  "file_size_bytes": null,
  "status": "generating",
  "created_at": "2026-04-15T08:00:00Z"
}
```

**Errors**:
- `400` — `{"detail": "User has no tenant"}`
- `404` — `{"detail": "Report not found"}`

---

## 12. Slot Status — Add "accepted" to Schema Reference

**Current state**: `POST /slots` returns `"status": "accepted"` (API Manual §6), but the Slot Status Values reference table (API Manual §18) only lists: `pending`, `processing`, `evaluated`, `unclear`, `failed`. The frontend TypeScript type and filter dropdown also omit it.

**Suggested fixes**:

1. **API Manual §18** — Add `accepted` to the Slot Status Values table:
   | `accepted` | Slot uploaded, awaiting processing queue assignment |

2. **Frontend** (`portal/src/types/index.ts:15`) — Add `"accepted"` to the `SlotStatus` type union.

3. **Frontend** (`portal/src/app/(app)/slots/page.tsx:17-24`) — Add "Accepted" option to the status filter dropdown.

---

## 13. Standardize HTTP 402 Error Format

**Current state**: HTTP 402 (Plan Limit Exceeded) errors return a non-standard format:
```json
{"error": "plan_limit_exceeded", "message": "Daily slot quota exceeded"}
```

All other errors use the standard `{"detail": "..."}` format. The frontend error handlers (`portal/src/hooks/useAdmin.ts`, `useNotes.ts`, `useUsers.ts`) only read `err?.response?.data?.detail`, so 402 messages display as generic errors instead of the actual quota message.

**Suggested**: Standardize 402 errors to use the `detail` format:

```json
{"detail": "Daily slot quota exceeded"}
```

**Alternative**: Keep current format but also add a `detail` field:
```json
{"error": "plan_limit_exceeded", "message": "Daily slot quota exceeded", "detail": "Daily slot quota exceeded"}
```

**Notes**: If changing the API format, update `next-steps.md` seed data and Postman collection accordingly. If keeping the current format, update the frontend error handlers to also check `err?.response?.data?.message`.

---

## Priority

1. **High**: #1 (Registration), #2 (Google OAuth), #5 (Permissions GET)
2. **Medium**: #3 (Provider API key), #4 (Model management), #6 (Audit log format), #9 (Notification settings), #10 (Permissions schema), #11 (Report detail docs), #13 (402 error format)
3. **Low**: #7 (Dashboard trends), #12 (accepted status docs)
4. **No change**: #8 (Terminal ping)
