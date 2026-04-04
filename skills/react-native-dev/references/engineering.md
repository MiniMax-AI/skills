# Engineering Reference

Project structure, tooling, builds, releases, and platform integration for Expo / React Native.

## Project Structure

### Standard Layout

```
my-app/
  app/                        File-based routing (Expo Router)
    _layout.tsx               Root layout: providers, fonts, NativeTabs
    index.tsx                 → /
    (tabs)/
      _layout.tsx             Tab navigator
      home.tsx                → /home
      profile.tsx             → /profile
    (auth)/
      login.tsx               → /login (group, not in URL)
      register.tsx            → /register
    user/
      [id].tsx                → /user/:id
      [id]/
        posts.tsx             → /user/:id/posts
    api/
      users+api.ts            → /api/users (server route)
      users/[id]+api.ts       → /api/users/:id
  components/                 Reusable UI components
    ui/                       Primitive components (Button, Input, Card)
    shared/                   Composed components (UserAvatar, PostCard)
  hooks/                      Custom React hooks
  stores/                     Zustand / Jotai stores
  services/                   API client, external service wrappers
  utils/                      Pure utility functions
  constants/                  App-wide constants (colors, spacing, config)
  types/                      Shared TypeScript types/interfaces
  assets/                     Static assets (images, fonts, icons)
  scripts/                    Build/dev helper scripts
  app.json                    Expo config
  eas.json                    EAS Build config
  tsconfig.json               TypeScript config with path aliases
  .env                        Environment variables
  .env.development
  .env.production
```

### Route Conventions

| File | Route | Notes |
|------|-------|-------|
| `app/index.tsx` | `/` | Home/root |
| `app/about.tsx` | `/about` | Static route |
| `app/user/[id].tsx` | `/user/:id` | Dynamic segment |
| `app/user/[...rest].tsx` | `/user/*` | Catch-all |
| `app/(tabs)/home.tsx` | `/home` | Group (not in URL) |
| `app/(a,b)/shared.tsx` | Shared between tabs `a` and `b` | Multi-group |
| `app/_layout.tsx` | Layout wrapper | No route |
| `app/+not-found.tsx` | 404 page | |
| `app/api/users+api.ts` | `/api/users` | Server route |

**Rules**:
- Routes only in `app/` — no components, types, or utils
- Always have a route matching `/`
- Use kebab-case filenames (`user-profile.tsx`, not `UserProfile.tsx`)
- Remove old route files when restructuring

### Path Aliases

```json
// tsconfig.json
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "paths": {
      "@/*": ["./*"],
      "@components/*": ["./components/*"],
      "@hooks/*": ["./hooks/*"],
      "@stores/*": ["./stores/*"],
      "@services/*": ["./services/*"],
      "@utils/*": ["./utils/*"],
      "@constants/*": ["./constants/*"],
      "@types/*": ["./types/*"]
    }
  }
}
```

```tsx
// ✗ Relative imports — fragile, change with file moves
import { Button } from "../../../components/ui/Button";

// ✓ Alias imports — stable
import { Button } from "@components/ui/Button";
```

Metro resolves `paths` and `baseUrl` from `tsconfig.json` natively — no extra config needed. If using a non-Metro bundler, install `babel-plugin-module-resolver`:

```js
// babel.config.js — only needed for non-Metro bundlers
module.exports = {
  presets: ["babel-preset-expo"],
  plugins: [
    ["module-resolver", {
      root: ["./"],
      alias: {
        "@": "./",
        "@components": "./components",
        "@hooks": "./hooks",
        "@stores": "./stores",
        "@services": "./services",
      },
    }],
  ],
};
```

### Components Organization

```
components/
  ui/                         Atomic components
    Button.tsx
    Input.tsx
    Card.tsx
    Badge.tsx
    index.ts                  Barrel export
  shared/                     Composed components
    UserAvatar.tsx
    PostCard.tsx
    EmptyState.tsx
  layout/                     Layout components
    Screen.tsx                SafeArea wrapper
    Header.tsx
```

```tsx
// components/ui/index.ts — barrel export
export { Button } from "./Button";
export { Input } from "./Input";
export { Card } from "./Card";

// Usage
import { Button, Input, Card } from "@components/ui";
```

### Design System

```
constants/
  colors.ts                   Color palette + semantic colors
  spacing.ts                  8pt grid spacing values
  typography.ts               Font families, sizes, weights
  theme.ts                    Combined theme object
```

```tsx
// constants/colors.ts
export const colors = {
  primary: "#6200EE",
  secondary: "#03DAC6",
  background: "#FFFFFF",
  surface: "#F5F5F5",
  error: "#B00020",
  text: { primary: "#000000DE", secondary: "#0000008A" },
} as const;

// constants/spacing.ts — 8pt grid
export const spacing = {
  xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48,
} as const;

// constants/typography.ts
export const typography = {
  sizes: { xs: 12, sm: 14, md: 16, lg: 20, xl: 24, xxl: 32 },
  weights: { regular: "400", medium: "500", semibold: "600", bold: "700" },
} as const;
```

### Services Layer

```
services/
  api/
    client.ts               Base fetch client with auth headers
    users.ts                User-related API calls
    posts.ts                Post-related API calls
  storage/
    secure-store.ts         Wrapper for expo-secure-store
    async-storage.ts        Wrapper for AsyncStorage
  notifications/
    push.ts                 Expo push notification helpers
```

```tsx
// services/api/client.ts
const BASE_URL = process.env.EXPO_PUBLIC_API_URL!;

export const api = {
  get: <T,>(path: string, token?: string) =>
    fetch(`${BASE_URL}${path}`, {
      headers: { Authorization: token ? `Bearer ${token}` : "" },
    }).then(async (r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json() as Promise<T>;
    }),
  // post/put/delete follow same pattern — add method, Content-Type, JSON.stringify(body)
};
```

### Monorepo

```
my-monorepo/
  apps/
    mobile/                 Expo app (all native deps here)
      package.json
      app.json
    web/                    Next.js app
      package.json
  packages/
    ui/                     Shared UI components (no native deps)
      package.json
    utils/                  Shared utilities (no native deps)
      package.json
    types/                  Shared TypeScript types
      package.json
  package.json              Root workspace config
```

```json
// Root package.json
{
  "private": true,
  "workspaces": ["apps/*", "packages/*"],
  "scripts": {
    "mobile": "yarn workspace @my/mobile start",
    "web": "yarn workspace @my/web dev"
  }
}
```

**Monorepo rules**:
- **Keep native dependencies in the app package** (`apps/mobile`) — never in shared packages
- Use a single version of each dependency across all packages
- Shared packages should be pure JS/TS only

### Environment Variables

```bash
# .env (committed, non-sensitive defaults)
EXPO_PUBLIC_APP_NAME=MyApp
EXPO_PUBLIC_API_VERSION=v1

# .env.development (local only, gitignored)
EXPO_PUBLIC_API_URL=http://localhost:3000

# .env.production (CI/CD only, gitignored)
EXPO_PUBLIC_API_URL=https://api.production.example.com
```

```tsx
// types/env.d.ts
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      EXPO_PUBLIC_API_URL: string;
      EXPO_PUBLIC_APP_NAME: string;
    }
  }
}
export {};
```

### Custom Fonts

```bash
npx expo install expo-font
```

```json
// app.json — config plugin (preferred over manual linking)
{
  "expo": {
    "plugins": [
      ["expo-font", { "fonts": ["./assets/fonts/Inter-Regular.ttf"] }]
    ]
  }
}
```

```tsx
// app/_layout.tsx
import { useFonts } from "expo-font";
import { SplashScreen } from "expo-router";

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded] = useFonts({ "Inter-Regular": require("../assets/fonts/Inter-Regular.ttf") });
  useEffect(() => { if (loaded) SplashScreen.hideAsync(); }, [loaded]);
  if (!loaded) return null;
  return <Stack />;
}
```

## Development Builds

Expo Go (`npx expo start`) covers most use cases out of the box. Switch to a custom dev client when your project uses native code that Expo Go doesn't bundle — for example, a local Expo module in `modules/`, an Apple target (widget, app clip), or a community native library that isn't pre-installed in Expo Go.

### Creating a Dev Client

```bash
# Option A — cloud build, push to TestFlight / internal distribution
eas build -p ios --profile development --submit

# Option B — build locally (requires Xcode / Android Studio)
eas build -p ios --profile development --local
```

After installing on the device or simulator, connect with:

```bash
npx expo start --dev-client
```

### eas.json Profile

```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "autoIncrement": true
    }
  }
}
```

## Upgrading the SDK

### Routine Upgrade

```bash
npx expo install expo@latest --fix   # bumps Expo + aligns peer deps
npx expo-doctor                       # surfaces remaining mismatches
```

Then test on both platforms and rebuild the dev client if you use one.

### Trying a Pre-release

Pre-release versions are tagged `@next` on npm:

```bash
npx expo install expo@next --fix
```

### Notable Changes Across SDK Versions

| Version | What Changed |
|---------|-------------|
| SDK 53 | New Architecture on by default; Expo Go requires it; `autoprefixer` no longer needed |
| SDK 54 | React 19 (`use()` replaces `useContext`, `<Context>` replaces `<Context.Provider>`, `forwardRef` removed); React Compiler available; `EXPO_USE_FAST_RESOLVER` removed |
| SDK 55 | NativeTabs API updated — Icon/Label/Badge accessed via `NativeTabs.Trigger.*` |
| Ongoing | `expo-av` deprecated in favor of `expo-audio` + `expo-video` |

### React 19 Patterns (SDK 54+)

```tsx
// Context
import { use, createContext } from "react";
const ThemeCtx = createContext("light");
// consume: const theme = use(ThemeCtx);
// provide: <ThemeCtx value="dark">...</ThemeCtx>

// Refs — no more forwardRef
function Field({ ref, ...props }: Props & { ref?: React.Ref<TextInput> }) {
  return <TextInput ref={ref} {...props} />;
}
```

### Opting Out of New Architecture

If a third-party library breaks under the New Architecture:

```json
{ "expo": { "newArchEnabled": false } }
```

Check compatibility at [reactnative.directory](https://reactnative.directory).

## Releasing

### Build Profiles

A typical `eas.json` has three tiers:

```json
{
  "cli": { "version": ">= 16.0.1", "appVersionSource": "remote" },
  "build": {
    "development": { "developmentClient": true, "distribution": "internal", "autoIncrement": true },
    "preview":     { "distribution": "internal", "autoIncrement": true },
    "production":  { "autoIncrement": true, "ios": { "resourceClass": "m-medium" } }
  }
}
```

### Building & Submitting

```bash
# Build for both platforms
eas build -p ios --profile production
eas build -p android --profile production

# Build + submit in one step
eas build -p ios --profile production --submit

# Or submit a finished build separately
eas submit -p ios
eas submit -p android
```

### Store Submission Notes

**iOS** — Run `eas credentials` to set up signing. Create the app record in App Store Connect, fill metadata, then `--submit` pushes the build to TestFlight automatically.

**Android** — Create a Google Play service account, download its JSON key, and reference it in `eas.json` under `submit.production.android.serviceAccountKeyPath`. The first build must be uploaded manually through Play Console; subsequent builds use `eas submit`.

### Over-the-Air Updates

For JS-only changes (no new native code), skip the full build/review cycle:

```bash
npx expo install expo-updates
eas update --branch production --message "Fix checkout rounding error"
```

### Web Hosting

```bash
npx expo export -p web
eas deploy              # preview URL
eas deploy --prod       # production
```

## CI/CD with EAS Workflows

Workflow files live in `.eas/workflows/` and follow a YAML schema:

```yaml
# .eas/workflows/release.yml
name: Release to stores

on:
  push:
    branches: [main]

jobs:
  build:
    type: build
    params:
      platform: all
      profile: production

  submit:
    type: submit
    needs: [build]
    params:
      platform: all
      profile: production
```

```yaml
# .eas/workflows/pr-check.yml
name: PR check

on:
  pull_request:
    branches: [main]

jobs:
  preview-build:
    type: build
    params:
      platform: all
      profile: preview
```

## DOM Components

The `"use dom"` directive lets you render web-only code inside a WebView on native while running it as standard DOM on web. Useful for libraries that depend on browser APIs (chart libraries, rich text editors, syntax highlighters).

```tsx
// components/RichPreview.tsx
"use dom";

import ReactMarkdown from "react-markdown";

export default function RichPreview({ markdown }: { markdown: string }) {
  return <ReactMarkdown>{markdown}</ReactMarkdown>;
}
```

```tsx
// app/note/[id].tsx — native screen
import RichPreview from "@/components/RichPreview";

export default function NoteScreen() {
  const { content } = useNote();
  return (
    <ScrollView>
      <RichPreview markdown={content} />
    </ScrollView>
  );
}
```

Rules:
- `"use dom"` must be the first statement in the file
- One default export per file; cannot be mixed with native components
- Props must be serializable (strings, numbers, booleans, plain objects/arrays)
- Async function props bridge native actions into the webview (e.g., `onSave: (data) => Promise<void>`)
- Cannot be used in `_layout.tsx` files
- Router hooks that read native navigation state (`useLocalSearchParams`, `usePathname`, etc.) must be called in the native parent and passed as props
