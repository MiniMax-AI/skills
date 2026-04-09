# Networking Reference

Building a robust data layer for Expo apps: API clients, server state, authentication, and server-side routes.

## API Client

### Setup

Create a thin wrapper around `fetch` (or `expo/fetch` on SDK 53+) rather than installing axios. Build a generic `request<T>(path, init?)` function that:

- Prepends `process.env.EXPO_PUBLIC_API_URL` to the path
- Defaults `Content-Type: application/json`, merges caller headers
- On `!res.ok`, throws an error with `status` and `body` attached (use `Object.assign`) so callers can branch on HTTP status
- Returns `res.json() as Promise<T>`

Then export convenience methods: `api.get<T>(path)`, `api.post<T>(path, body)`, etc., each delegating to `request()` with the appropriate method and `JSON.stringify(body)`.

### Typed Errors

Distinguish network-level failures (no connectivity, DNS) from HTTP-level errors (4xx/5xx). The wrapper above attaches `status` and `body` to thrown errors so callers can branch:

```tsx
try {
  await api.post("/tasks", newTask);
} catch (err: any) {
  if (err.status === 409) {
    Alert.alert("Duplicate", "A task with that title already exists.");
  } else if (err.status === undefined) {
    Alert.alert("Offline", "Check your connection and try again.");
  }
}
```

## Server State (React Query)

### Provider

```tsx
// app/_layout.tsx
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";

const qc = new QueryClient({
  defaultOptions: { queries: { staleTime: 60_000 } },
});

export default function RootLayout() {
  return (
    <QueryClientProvider client={qc}>
      <Stack />
    </QueryClientProvider>
  );
}
```

### Reading Data

```tsx
function TaskList({ projectId }: { projectId: string }) {
  const { data: tasks, isPending, error } = useQuery({
    queryKey: ["projects", projectId, "tasks"],
    queryFn: () => api.get<Task[]>(`/projects/${projectId}/tasks`),
  });

  if (isPending) return <ActivityIndicator />;
  if (error) return <ErrorBanner message={error.message} />;

  return (
    <FlashList
      data={tasks}
      renderItem={({ item }) => <TaskRow task={item} />}
      estimatedItemSize={56}
    />
  );
}
```

### Writing Data

```tsx
function useCompleteTask(projectId: string) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => api.put(`/tasks/${taskId}`, { done: true }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects", projectId, "tasks"] }),
  });
}
```

### Optimistic Updates

For snappy UIs, update the cache before the server confirms:

```tsx
const toggle = useMutation({
  mutationFn: (task: Task) => api.put(`/tasks/${task.id}`, { done: !task.done }),
  onMutate: async (task) => {
    await qc.cancelQueries({ queryKey });
    const prev = qc.getQueryData<Task[]>(queryKey);
    qc.setQueryData<Task[]>(queryKey, (old) =>
      old?.map((t) => (t.id === task.id ? { ...t, done: !t.done } : t)),
    );
    return { prev };
  },
  onError: (_err, _task, ctx) => qc.setQueryData(queryKey, ctx?.prev),
  onSettled: () => qc.invalidateQueries({ queryKey }),
});
```

## Authentication

### Storing Credentials

Use `expo-secure-store` for any token or secret. AsyncStorage is unencrypted and readable on rooted/jailbroken devices.

```tsx
import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "session_token";

export async function saveToken(token: string) {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
}
export async function getToken() {
  return SecureStore.getItemAsync(TOKEN_KEY);
}
export async function clearToken() {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
}
```

### Injecting Auth Headers

Extend the API client to attach the token automatically:

```tsx
export async function authRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getToken();
  return request<T>(path, {
    ...init,
    headers: { ...init?.headers, ...(token && { Authorization: `Bearer ${token}` }) },
  });
}
```

### Refreshing Expired Tokens

Avoid stampeding refresh calls when multiple requests discover the token is expired simultaneously. Hold a single in-flight refresh promise and let all waiters share it:

```tsx
let pending: Promise<string> | null = null;

async function getFreshToken(): Promise<string> {
  if (pending) return pending;

  pending = (async () => {
    const refresh = await SecureStore.getItemAsync("refresh_token");
    const { accessToken } = await api.post<{ accessToken: string }>("/auth/refresh", { refresh });
    await saveToken(accessToken);
    return accessToken;
  })();

  try {
    return await pending;
  } finally {
    pending = null;
  }
}
```

## Environment Variables

```bash
# .env.development
EXPO_PUBLIC_API_URL=http://localhost:3000

# .env.production
EXPO_PUBLIC_API_URL=https://api.production.example.com
```

- The `EXPO_PUBLIC_` prefix makes a variable available in client JS (inlined at build time)
- Variables **without** the prefix are only accessible in server-side API routes
- Never expose database credentials or write-capable API keys via `EXPO_PUBLIC_`
- Restart the dev server after editing `.env` files

Type the variables for autocomplete:

```tsx
// env.d.ts
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      EXPO_PUBLIC_API_URL: string;
    }
  }
}
export {};
```

## Offline & Connectivity

Track device connectivity with `@react-native-community/netinfo` and wire it into React Query so queries automatically pause offline and resume on reconnect:

```tsx
// app/_layout.tsx (once, at startup)
import { onlineManager } from "@tanstack/react-query";
import NetInfo from "@react-native-community/netinfo";

onlineManager.setEventListener((setOnline) =>
  NetInfo.addEventListener((state) => setOnline(!!state.isConnected)),
);
```

To show an in-app banner, subscribe separately:

```tsx
function useOnline() {
  const [online, setOnline] = useState(true);
  useEffect(() => NetInfo.addEventListener((s) => setOnline(!!s.isConnected)), []);
  return online;
}
```

## Request Lifecycle

### Cancellation

When a component unmounts mid-request, abort the in-flight fetch to avoid setting state on an unmounted component:

```tsx
useEffect(() => {
  const ac = new AbortController();
  api.get(`/projects/${id}`, { signal: ac.signal }).then(setProject);
  return () => ac.abort();
}, [id]);
```

React Query handles cancellation automatically for queries — no extra work needed.

### Retries

React Query retries failed queries by default (3 attempts with exponential backoff). For mutations or non-React-Query code, implement manually:

```tsx
async function withRetry<T>(fn: () => Promise<T>, attempts = 3): Promise<T> {
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === attempts - 1) throw err;
      await new Promise((r) => setTimeout(r, 1000 * 2 ** i));
    }
  }
  throw new Error("unreachable");
}
```

## Server-Side API Routes

Expo Router supports `+api.ts` files that run on the server (deployed to EAS Hosting / Cloudflare Workers). Use them when you need to keep secrets server-side, proxy third-party APIs, or run database queries.

### Conventions

```
app/
  api/
    health+api.ts              → GET /api/health
    projects+api.ts            → GET|POST /api/projects
    projects/[id]+api.ts       → GET|PUT|DELETE /api/projects/:id
    webhooks/payments+api.ts   → POST /api/webhooks/payments
```

Export a named function per HTTP method:

```ts
// app/api/projects+api.ts
export async function GET(req: Request) {
  const url = new URL(req.url);
  const cursor = url.searchParams.get("cursor");
  const rows = await db.query("SELECT * FROM projects WHERE id > ? LIMIT 20", [cursor ?? 0]);
  return Response.json(rows);
}

export async function POST(req: Request) {
  const { name, description } = await req.json();
  const [row] = await db.insert(projectsTable).values({ name, description }).returning();
  return Response.json(row, { status: 201 });
}
```

### Secrets

Variables **without** the `EXPO_PUBLIC_` prefix are server-only:

```ts
// app/api/ai/summarize+api.ts
const LLM_KEY = process.env.LLM_API_KEY; // never reaches the client bundle

export async function POST(req: Request) {
  const { text } = await req.json();
  const res = await fetch("https://api.llm.example.com/v1/chat", {
    method: "POST",
    headers: { Authorization: `Bearer ${LLM_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ messages: [{ role: "user", content: `Summarize: ${text}` }] }),
  });
  return Response.json(await res.json());
}
```

### Webhooks

```ts
// app/api/webhooks/payments+api.ts — verify signature, then handle event
const event = stripe.webhooks.constructEvent(rawBody, sig, process.env.STRIPE_WH_SECRET!);
if (event.type === "checkout.session.completed") {
  await activateSubscription(event.data.object.customer as string);
}
```

### Protecting Routes

```ts
// lib/require-auth.ts — extract and verify JWT from Authorization header, throw Response on failure
export async function requireAuth(req: Request): Promise<string> {
  const header = req.headers.get("Authorization");
  if (!header?.startsWith("Bearer "))
    throw Response.json({ error: "unauthorized" }, { status: 401 });
  const uid = await verifyJwt(header.slice(7));
  if (!uid) throw Response.json({ error: "invalid token" }, { status: 401 });
  return uid;
}
// Usage in route: const uid = await requireAuth(req);
```

### Deploying

```bash
npx expo export
eas deploy            # preview
eas deploy --prod     # production

# Set server-only secrets
eas env:create --name LLM_API_KEY --value "sk-..." --environment production
```

API routes run on Cloudflare Workers — no `fs` module, 30 s CPU limit, use Web APIs (`fetch`, `crypto.subtle`) instead of Node built-ins.
