# State Management Reference

Patterns for local, shared, and server state in React Native / Expo apps.

## Decision Guide

| State Type | Solution |
|------------|----------|
| Local UI state (toggle, input) | `useState` / `useReducer` |
| Shared app-wide state | Zustand or Jotai |
| Server/async data | React Query (TanStack Query) |
| Form state | React Hook Form (see forms.md) |
| Auth / session | Zustand + `expo-secure-store` |

**Avoid**: Redux for new projects (boilerplate), Context for high-frequency updates (re-render overhead).

## useState / useReducer

```tsx
// Simple toggle
const [isOpen, setIsOpen] = useState(false);

// Complex local state — useReducer
type State = { count: number; status: "idle" | "loading" | "error" };
type Action = { type: "increment" } | { type: "setStatus"; payload: State["status"] };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "increment": return { ...state, count: state.count + 1 };
    case "setStatus": return { ...state, status: action.payload };
  }
}

const [state, dispatch] = useReducer(reducer, { count: 0, status: "idle" });
dispatch({ type: "increment" });
```

## Zustand (Shared State)

```bash
npx expo install zustand
```

```tsx
// stores/settings-store.ts
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import AsyncStorage from "@react-native-async-storage/async-storage";

interface SettingsStore {
  theme: "light" | "dark";
  locale: string;
  setTheme: (theme: "light" | "dark") => void;
  setLocale: (locale: string) => void;
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      theme: "light",
      locale: "en",
      setTheme: (theme) => set({ theme }),
      setLocale: (locale) => set({ locale }),
    }),
    {
      name: "settings-storage",
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);

// Usage
const { theme, setTheme } = useSettingsStore();
const locale = useSettingsStore((s) => s.locale); // Selector — minimizes re-renders
```

```tsx
// stores/cart-store.ts
interface CartStore {
  items: CartItem[];
  add: (product: Product) => void;
  remove: (id: string) => void;
  clear: () => void;
  total: () => number;
}

export const useCartStore = create<CartStore>()((set, get) => ({
  items: [],
  add: (product) => set((s) => ({
    items: [...s.items, { product, quantity: 1 }],
  })),
  remove: (id) => set((s) => ({
    items: s.items.filter((i) => i.product.id !== id),
  })),
  clear: () => set({ items: [] }),
  total: () => get().items.reduce((sum, i) => sum + i.product.price * i.quantity, 0),
}));
```

## Jotai (Atomic State)

```bash
npx expo install jotai
```

```tsx
// atoms/user-atoms.ts
import { atom } from "jotai";
import { atomWithStorage, createJSONStorage } from "jotai/utils";
import AsyncStorage from "@react-native-async-storage/async-storage";

const storage = createJSONStorage(() => AsyncStorage);

export const userAtom = atom<User | null>(null);
export const themeAtom = atomWithStorage<"light" | "dark">("theme", "light", storage);

// Derived atom — computed from others
export const isAdminAtom = atom((get) => get(userAtom)?.role === "admin");
```

```tsx
// Usage — component only re-renders when its atoms change
import { useAtom, useAtomValue, useSetAtom } from "jotai";

function Header() {
  const user = useAtomValue(userAtom);         // read-only
  const setTheme = useSetAtom(themeAtom);      // write-only
  const [theme, setThemeRW] = useAtom(themeAtom); // read + write
  return <Text>{user?.name}</Text>;
}
```

**Zustand vs Jotai**:
- **Zustand** — store-based, better for related state with actions (auth, cart)
- **Jotai** — atom-based, better for independent values, fine-grained subscriptions, avoids re-renders

## React Query (Server State)

See [networking.md](networking.md) for full reference. Key patterns:

```tsx
// Queries — read
const { data, isLoading } = useQuery({ queryKey: ["users"], queryFn: fetchUsers });

// Mutations — write
const mutation = useMutation({
  mutationFn: createUser,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
});

// Optimistic update
const mutation = useMutation({
  mutationFn: updateUser,
  onMutate: async (newUser) => {
    await queryClient.cancelQueries({ queryKey: ["user", newUser.id] });
    const prev = queryClient.getQueryData(["user", newUser.id]);
    queryClient.setQueryData(["user", newUser.id], newUser);
    return { prev };
  },
  onError: (_err, variables, context) => {
    queryClient.setQueryData(["user", variables.id], context?.prev);
  },
});
```

## Minimize Re-renders

### Zustand Selectors

```tsx
// ✗ Wrong — re-renders on any store change
const store = useAuthStore();

// ✓ Correct — re-renders only when user changes
const user = useAuthStore((s) => s.user);
const logout = useAuthStore((s) => s.logout); // Actions are stable references
```

### Dispatcher Pattern

```tsx
// ✗ Wrong — passes callbacks that recreate on every render
function Parent() {
  const [count, setCount] = useState(0);
  return <Child onIncrement={() => setCount(c => c + 1)} />;
}

// ✓ Correct — dispatcher reference is stable
function Parent() {
  const [count, dispatch] = useReducer(reducer, 0);
  return <Child dispatch={dispatch} />;
}
```

### React Compiler (SDK 54+)

With React Compiler enabled, `memo`, `useCallback`, and `useMemo` are often unnecessary:

```json
// app.json
{ "expo": { "experiments": { "reactCompiler": true } } }
```

## Context (Use Sparingly)

Context is suitable for infrequently-changing values (theme, locale, auth status). **Avoid** for high-frequency updates like scroll position or form input.

```tsx
const ThemeContext = createContext<"light" | "dark">("light");

function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  return <ThemeContext value={theme}>{children}</ThemeContext>; // React 19+
}

// Consume
const theme = use(ThemeContext); // React 19+
```

## Fallback on First Render

```tsx
// ✓ Always show fallback while async state loads
function UserProfile({ userId }: { userId: string }) {
  const { data, isLoading } = useQuery({ queryKey: ["user", userId], queryFn: () => fetchUser(userId) });
  if (isLoading) return <UserProfileSkeleton />;
  if (!data) return null;
  return <Profile user={data} />;
}
```
