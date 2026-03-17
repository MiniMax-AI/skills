---
name: fullstack-dev-api-design
description: "API design patterns and best practices. Use when creating endpoints, choosing methods/status codes, implementing pagination, or writing OpenAPI specs. Prevents common REST/GraphQL/gRPC mistakes."
license: MIT
metadata:
  version: "2.0.0"
  sources:
    - Microsoft REST API Guidelines
    - Google API Design Guide
    - Zalando RESTful API Guidelines
    - JSON:API Specification
    - RFC 9457 (Problem Details for HTTP APIs)
    - RFC 9110 (HTTP Semantics)
---

# API Design Guidelines

Framework-agnostic API design guide for backend and full-stack engineers. 50+ rules across 10 categories, prioritized by impact. Covers REST, GraphQL, and gRPC.

## Scope

**USE this skill when:**
- Designing a new API or adding endpoints
- Reviewing API pull requests
- Choosing between REST / GraphQL / gRPC
- Writing OpenAPI specifications
- Migrating or versioning an existing API

**NOT for:**
- Framework-specific implementation details (use your framework's own skill/docs)
- Frontend data fetching patterns (use React Query / SWR docs)
- Authentication implementation details (use your auth library's docs)
- Database schema design (→ `database-schema-design`)

## Context Required

Before applying this skill, gather:

| Required | Optional |
|----------|----------|
| Target consumers (browser, mobile, service) | Existing API conventions in the project |
| Expected request volume (RPS estimate) | Current OpenAPI / Swagger spec |
| Authentication method (JWT, API key, OAuth) | Rate limiting requirements |
| Data model / domain entities | Caching strategy |

---

## Quick Start Checklist

New API endpoint? Run through this before writing code:

- [ ] Resource named as **plural noun** (`/orders`, not `/getOrders`)
- [ ] URL in **kebab-case**, body fields in **camelCase**
- [ ] Correct **HTTP method** (GET=read, POST=create, PUT=replace, PATCH=partial, DELETE=remove)
- [ ] Correct **status code** (201 Created, 422 Validation, 404 Not Found…)
- [ ] Error response follows **RFC 9457** envelope
- [ ] **Pagination** on all list endpoints (default 20, max 100)
- [ ] **Authentication** required (Bearer token, not query param)
- [ ] **Request ID** in response header (`X-Request-Id`)
- [ ] **Rate limit** headers included
- [ ] Endpoint documented in **OpenAPI spec**

---

## Quick Navigation

| Need to… | Jump to |
|----------|---------|
| Name a resource URL | [1. Resource Modeling](#1-resource-modeling-critical) |
| Pick HTTP method + status code | [3. HTTP Methods & Status Codes](#3-http-methods--status-codes-critical) |
| Format error responses | [4. Error Handling](#4-error-handling-high) |
| Add pagination or filtering | [6. Pagination & Filtering](#6-pagination--filtering-high) |
| Choose API style (REST vs GraphQL vs gRPC) | [10. API Style Decision](#10-api-style-decision-tree) |
| Version an existing API | [7. Versioning](#7-versioning-medium-high) |
| Avoid common mistakes | [Anti-Patterns](#anti-patterns-checklist) |

---

## 1. Resource Modeling (CRITICAL)

### Core Rules

```
✅ /users                         — plural noun
✅ /users/{id}/orders              — 1 level nesting
✅ /reviews?orderId={oid}          — flatten deep nesting with query params

❌ /getUsers                       — verb in URL
❌ /user                           — singular
❌ /users/{uid}/orders/{oid}/items/{iid}/reviews  — 3+ levels deep
```

**Max nesting: 2 levels.** Beyond that, promote to top-level resource with filters.

### Domain Alignment

Resources map to **domain concepts**, not database tables:

```
✅ /checkout-sessions       (domain aggregate)
✅ /shipping-labels          (domain concept)

❌ /tbl_order_header          (database table leak)
❌ /join_user_role            (internal schema leak)
```

---

## 2. URL & Naming (CRITICAL)

| Context | Convention | Example |
|---------|-----------|---------|
| URL path | kebab-case | `/order-items` |
| JSON body fields | camelCase | `{ "firstName": "Jane" }` |
| Query params | camelCase or snake_case (be consistent) | `?sortBy=createdAt` |
| Headers | Train-Case | `X-Request-Id` |

**Python exception:** If your entire stack is Python/snake_case, you MAY use `snake_case` in JSON — but be **consistent across all endpoints**.

```
✅ GET /users          ❌ GET /users/
✅ GET /reports/annual  ❌ GET /reports/annual.json
✅ POST /users          ❌ POST /users/create
```

---

## 3. HTTP Methods & Status Codes (CRITICAL)

### Method Semantics

| Method | Semantics | Idempotent | Safe | Request Body |
|--------|-----------|-----------|------|-------------|
| GET | Read | ✅ | ✅ | ❌ Never |
| POST | Create / Action | ❌ | ❌ | ✅ Always |
| PUT | Full replace | ✅ | ❌ | ✅ Always |
| PATCH | Partial update | ❌* | ❌ | ✅ Always |
| DELETE | Remove | ✅ | ❌ | ❌ Rarely |

### Status Code Quick Reference

**Success:**

| Code | When | Response Body |
|------|------|--------------|
| 200 OK | GET, PUT, PATCH success | Resource / result |
| 201 Created | POST created resource | Created resource + `Location` header |
| 202 Accepted | Async operation started | Job ID / status URL |
| 204 No Content | DELETE success, PUT with no body | None |

**Client Errors:**

| Code | When | Key Distinction |
|------|------|-----------------|
| 400 Bad Request | Malformed syntax | Can't even parse |
| 401 Unauthorized | Missing / invalid auth | "Who are you?" |
| 403 Forbidden | Authenticated, no permission | "I know you, but no" |
| 404 Not Found | Resource doesn't exist | Also use to hide 403 |
| 409 Conflict | Duplicate, version mismatch | State conflict |
| 422 Unprocessable | Valid syntax, failed validation | Semantic errors |
| 429 Too Many Requests | Rate limit hit | Include `Retry-After` |

**Server Errors:** 500 (unexpected), 502 (upstream fail), 503 (overloaded), 504 (upstream timeout)

---

## 4. Error Handling (HIGH)

### Standard Error Envelope (RFC 9457)

Every error response uses this format:

```json
{
  "type": "https://api.example.com/errors/insufficient-funds",
  "title": "Insufficient Funds",
  "status": 422,
  "detail": "Account balance $10.00 is less than withdrawal $50.00.",
  "instance": "/transactions/txn_abc123",
  "request_id": "req_7f3a8b2c",
  "errors": [
    { "field": "amount", "message": "Exceeds balance", "code": "INSUFFICIENT_BALANCE" }
  ]
}
```

### Multi-Language Implementation

**TypeScript (Express):**
```typescript
class AppError extends Error {
  constructor(
    public readonly title: string,
    public readonly status: number,
    public readonly detail: string,
    public readonly code: string,
  ) { super(detail); }
}

// Middleware
app.use((err, req, res, next) => {
  if (err instanceof AppError) {
    return res.status(err.status).json({
      type: `https://api.example.com/errors/${err.code}`,
      title: err.title, status: err.status,
      detail: err.detail, request_id: req.id,
    });
  }
  res.status(500).json({ title: 'Internal Error', status: 500, request_id: req.id });
});
```

**Python (FastAPI):**
```python
from fastapi import Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(self, title: str, status: int, detail: str, code: str):
        self.title, self.status, self.detail, self.code = title, status, detail, code

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status, content={
        "type": f"https://api.example.com/errors/{exc.code}",
        "title": exc.title, "status": exc.status,
        "detail": exc.detail, "request_id": request.state.request_id,
    })
```

### Iron Rules

```
✅ Return RFC 9457 error envelope for ALL errors
✅ Include request_id in every error response
✅ Return per-field validation errors in `errors` array

❌ Never expose stack traces in production
❌ Never return 200 for errors
❌ Never swallow errors silently
```

---

## 5. Authentication & Authorization (HIGH)

```
✅ Authorization: Bearer eyJhbGci...      (header)
❌ GET /users?token=eyJhbGci...            (URL — appears in logs)

✅ 401 → "Who are you?"  (missing/invalid credentials)
✅ 403 → "You can't do this"  (authenticated, no permission)
✅ 404 → Hide resource existence  (use instead of 403 when needed)
```

**Rate Limit Headers (always include):**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1625097600
Retry-After: 30
```

---

## 6. Pagination & Filtering (HIGH)

### Cursor vs Offset

| Strategy | When | Pros | Cons |
|----------|------|------|------|
| **Cursor** (preferred) | Large/dynamic datasets | Consistent, no skips | Can't jump to page N |
| **Offset** | Small/stable datasets, admin UIs | Simple, page jumps | Drift on insert/delete |

**Cursor pagination response:**
```json
{
  "data": [...],
  "pagination": { "next_cursor": "eyJpZCI6MTIwfQ", "has_more": true }
}
```

**Offset pagination response:**
```json
{
  "data": [...],
  "pagination": { "page": 3, "per_page": 20, "total": 256, "total_pages": 13 }
}
```

**Always enforce:** Default 20 items, max 100 items.

### Standard Filter Patterns

```
GET /orders?status=shipped&created_after=2025-01-01&sort=-created_at&fields=id,status
```

| Pattern | Convention |
|---------|-----------|
| Exact match | `?status=shipped` |
| Range | `?price_gte=10&price_lte=100` |
| Date range | `?created_after=2025-01-01&created_before=2025-12-31` |
| Sort | `?sort=field` (asc), `?sort=-field` (desc) |
| Sparse fields | `?fields=id,name,email` |
| Search | `?q=search+term` |

---

## 7. Versioning (MEDIUM-HIGH)

| Strategy | Format | Best For |
|----------|--------|----------|
| **URL path** (recommended) | `/v1/users` | Public APIs |
| **Header** | `Api-Version: 2` | Internal APIs |
| **Query param** | `?version=2` | Legacy (avoid) |

**Non-breaking changes (no version bump):** New optional response fields, new endpoints, new optional params.

**Breaking changes (new version required):** Removing/renaming fields, changing types, stricter validation, removing endpoints.

**Deprecation headers:**
```
Sunset: Sat, 01 Mar 2026 00:00:00 GMT
Deprecation: true
Link: <https://api.example.com/v2/users>; rel="successor-version"
```

---

## 8. Request / Response Design (MEDIUM)

### Consistent Envelope

```json
{
  "data": { "id": "ord_123", "status": "pending", "total": 99.50 },
  "meta": { "request_id": "req_abc123", "timestamp": "2025-06-15T10:30:00Z" }
}
```

### Key Rules

| Rule | Correct | Wrong |
|------|---------|-------|
| Timestamps | `"2025-06-15T10:30:00Z"` (ISO 8601) | `"06/15/2025"` or `1718447400` |
| Public IDs | UUID `"550e8400-..."` | Auto-increment `42` |
| Null vs absent (PATCH) | `{ "nickname": null }` = clear field | Absent field = don't change |
| HATEOAS (public APIs) | `"links": { "cancel": "/orders/123/cancel" }` | No discoverability |

---

## 9. Documentation — OpenAPI (MEDIUM)

**Design-first workflow:**

```
1. Write OpenAPI 3.1 spec
2. Review spec with stakeholders
3. Generate server stubs + client SDKs
4. Implement handlers
5. Validate responses against spec in CI
```

Every endpoint documents: summary, all parameters, request body + examples, all response codes + schemas, auth requirements.

---

## 10. API Style Decision Tree

```
What kind of API?
│
├─ Browser + mobile clients, flexible queries
│   └─ GraphQL
│       Rules: DataLoader (no N+1), depth limit ≤7, Relay pagination
│
├─ Standard CRUD, public consumers, caching important
│   └─ REST (this guide)
│       Rules: Resources, HTTP methods, status codes, OpenAPI
│
├─ Service-to-service, high throughput, strong typing
│   └─ gRPC
│       Rules: Protobuf schemas, streaming for large data, deadlines
│
├─ Full-stack TypeScript, same team owns client + server
│   └─ tRPC
│       Rules: Shared types, no code generation needed
│
└─ Real-time bidirectional
    └─ WebSocket / SSE
        Rules: Heartbeat, reconnection, message ordering
```

---

## Anti-Patterns Checklist

| # | ❌ Don't | ✅ Do Instead |
|---|---------|--------------|
| 1 | Verbs in URLs (`/getUser`) | HTTP methods + noun resources |
| 2 | Return 200 for errors | Correct 4xx/5xx status codes |
| 3 | Mix naming styles | One convention per context |
| 4 | Expose database IDs | UUIDs for public identifiers |
| 5 | No pagination on lists | Always paginate (default 20) |
| 6 | Swallow errors silently | Structured RFC 9457 errors |
| 7 | Token in URL query | Authorization header |
| 8 | Deep nesting (3+ levels) | Flatten with query params |
| 9 | Break changes without version | Maintain compatibility or version |
| 10 | No rate limiting | Implement + communicate via headers |
| 11 | No request ID | `X-Request-Id` on every response |
| 12 | Stack traces in production | Safe error message + internal log |

---

## Common Issues

### Issue 1: "Should this be a new resource or a sub-resource?"

**Symptom:** URL path keeps growing (`/users/{id}/orders/{id}/items/{id}/reviews`)

**Rule:** If the child entity makes sense on its own, promote it. If it only exists within the parent context, keep it nested (max 2 levels).

```
/reviews?orderId=123      ✅  (reviews exist independently)
/orders/{id}/items         ✅  (items belong to orders, 1 level)
```

### Issue 2: "PUT or PATCH?"

**Symptom:** Team can't agree on update semantics.

**Rule:**
- PUT = client sends **complete** resource (missing fields → set to default/null)
- PATCH = client sends **only changed fields** (missing fields → unchanged)
- When unsure → **PATCH** (safer, less surprising)

### Issue 3: "400 or 422?"

**Symptom:** Inconsistent validation error codes.

**Rule:**
- 400 = can't parse request at all (malformed JSON, wrong content-type)
- 422 = parsed OK, but values fail validation (invalid email, negative quantity)
