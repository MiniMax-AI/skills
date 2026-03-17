# Environment & CORS Management

Patterns for managing environment variables, API URLs, and CORS configuration across frontend and backend stacks.

---

## Standard Environment Pattern

```
# .env.local (gitignored, for local dev)
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=ws://localhost:3001

# Staging (set in Vercel/CI)
NEXT_PUBLIC_API_URL=https://api-staging.example.com

# Production (set in Vercel/CI)
NEXT_PUBLIC_API_URL=https://api.example.com
```

---

## Environment Variable Rules

```
✅ API base URL from environment variable — NEVER hardcoded
✅ Prefix client-side vars with NEXT_PUBLIC_ (Next.js) or VITE_ (Vite)
✅ Backend URL = server-only env var (for SSR calls, not exposed to browser)
✅ CORS on backend: explicit list of allowed origins per environment

❌ Never use localhost URLs in production builds
❌ Never expose backend-only secrets with NEXT_PUBLIC_ prefix
❌ Never commit .env.local (commit .env.example with placeholders)
```

---

## CORS Configuration

```typescript
// Backend: environment-aware CORS
const ALLOWED_ORIGINS = {
  development: ['http://localhost:3000', 'http://localhost:5173'],
  staging: ['https://staging.example.com'],
  production: ['https://example.com', 'https://www.example.com'],
};

app.use(cors({
  origin: ALLOWED_ORIGINS[process.env.NODE_ENV || 'development'],
  credentials: true,  // needed for cookies (auth)
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
}));
```

---

## Common Issues

### Issue 1: "CORS error in browser but works in Postman"

**Cause:** CORS is a browser security feature. Postman/curl skip it.

**Fix:**
1. Backend must return `Access-Control-Allow-Origin: https://your-frontend.com`
2. For cookies/auth: `credentials: true` on both sides
3. Check that preflight `OPTIONS` request returns correct headers

### Issue 2: "Environment variable undefined in browser"

**Cause:** Missing `NEXT_PUBLIC_` or `VITE_` prefix for client-side access.

**Fix:** Client-side vars MUST have the framework prefix. Rebuild after adding new env vars (they are embedded at build time).

### Issue 3: "Works locally, fails in staging"

**Cause:** Different origins, missing CORS config for staging domain.

**Fix:** Add staging origin to `ALLOWED_ORIGINS`, verify env vars are set in deployment platform.
