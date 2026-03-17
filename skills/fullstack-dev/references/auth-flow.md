# Authentication Flow Patterns

Complete auth flow across frontend and backend. Covers JWT bearer flow, automatic token refresh, Next.js server-side auth, RBAC, and backend middleware order.

---

## JWT Bearer Flow (Most Common)

```
1. Login
   Client → POST /api/auth/login { email, password }
   Server → { accessToken (15min), refreshToken (7d, httpOnly cookie) }

2. Authenticated Requests
   Client → GET /api/orders  Authorization: Bearer <accessToken>
   Server → validates JWT → returns data

3. Token Refresh (transparent)
   Client → 401 received → POST /api/auth/refresh (cookie auto-sent)
   Server → new accessToken
   Client → retry original request with new token

4. Logout
   Client → POST /api/auth/logout
   Server → invalidate refresh token → clear cookie
```

---

## Frontend: Automatic Token Refresh

```typescript
// lib/api-client.ts — add to existing fetch wrapper
async function apiWithRefresh<T>(path: string, options: RequestInit = {}): Promise<T> {
  try {
    return await api<T>(path, options);
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      // Try refresh
      const refreshed = await api<{ accessToken: string }>('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',  // send httpOnly cookie
      });
      setAuthToken(refreshed.accessToken);
      // Retry original request
      return api<T>(path, options);
    }
    throw err;
  }
}
```

---

## Next.js: Server-Side Auth (App Router)

```typescript
// middleware.ts — protect routes server-side
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('session')?.value;
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  return NextResponse.next();
}

// app/dashboard/page.tsx — server component with auth
import { cookies } from 'next/headers';

export default async function Dashboard() {
  const token = (await cookies()).get('session')?.value;
  const user = await fetch(`${process.env.API_URL}/api/me`, {
    headers: { Authorization: `Bearer ${token}` },
  }).then(r => r.json());

  return <DashboardContent user={user} />;
}
```

---

## Backend: Standard Middleware Order

```
Request → 1.RequestID → 2.Logging → 3.CORS → 4.RateLimit → 5.BodyParse
       → 6.Auth → 7.Authz → 8.Validation → 9.Handler → 10.ErrorHandler → Response
```

---

## Backend: JWT Rules

```
✅ Short expiry access token (15min) + refresh token (server-stored)
✅ Minimal claims: userId, roles (not entire user object)
✅ Rotate signing keys periodically

❌ Never store tokens in localStorage (XSS risk)
❌ Never pass tokens in URL query params
```

---

## Backend: RBAC Pattern

```typescript
function authorize(...roles: Role[]) {
  return (req, res, next) => {
    if (!req.user) throw new UnauthorizedError();
    if (!roles.some(r => req.user.roles.includes(r))) throw new ForbiddenError();
    next();
  };
}
router.delete('/users/:id', authenticate, authorize('admin'), deleteUser);
```

---

## Auth Decision Table

| Method | When | Frontend |
|--------|------|----------|
| Session | Same-domain, SSR, Django templates | Django templates / htmx |
| JWT | Different domain, SPA, mobile | React, Vue, mobile apps |
| OAuth2 | Third-party login, API consumers | Any |

---

## Iron Rules

```
✅ Access token: short-lived (15min), in memory
✅ Refresh token: httpOnly cookie (XSS-safe)
✅ Automatic transparent refresh on 401
✅ Redirect to login when refresh fails

❌ Never store tokens in localStorage (XSS risk)
❌ Never send tokens in URL query params (logged)
❌ Never trust client-side auth checks alone (server must validate)
```

---

## Common Issues

### Issue 1: "Auth works on page load but breaks on navigation"

**Cause:** Token stored in component state (lost on unmount).

**Fix:** Store access token in a persistent location:
- React Context (survives navigation, lost on refresh)
- Cookie (survives refresh)
- React Query cache with `staleTime: Infinity` for session

### Issue 2: "CORS error with auth requests"

**Cause:** Missing `credentials: 'include'` on frontend or `credentials: true` on backend CORS config.

**Fix:**
1. Frontend: `fetch(url, { credentials: 'include' })`
2. Backend: `cors({ origin: 'https://your-frontend.com', credentials: true })`
3. Backend: explicit origin (not `*`) when using credentials
