---
name: react-native-dev
description: |
  React Native and Expo development guide covering components, styling, animations, navigation,
  state management, forms, networking, performance optimization, testing, native capabilities,
  and engineering (project structure, deployment, SDK upgrades, CI/CD).
  Use when: building React Native or Expo apps, implementing animations or native UI, managing
  state, fetching data, writing tests, optimizing performance, deploying to App Store/Play Store,
  setting up CI/CD, upgrading Expo SDK, or configuring Tailwind/NativeWind.
license: MIT
metadata:
  version: "1.0.0"
  category: mobile
  sources:
    - Expo documentation (docs.expo.dev)
    - React Native documentation (reactnative.dev)
    - EAS (Expo Application Services) documentation
---

# React Native & Expo Development Guide

A practical guide for building production-ready React Native and Expo applications. Covers UI, animations, state, testing, performance, and deployment.

## References

Consult these resources as needed:

- [references/navigation.md](references/navigation.md) — Expo Router: Stack, Tabs, NativeTabs (`headerLargeTitle`, `headerBackButtonDisplayMode`), links, modals, sheets, context menus
- [references/components.md](references/components.md) — FlashList patterns, `expo-image`, safe areas (`contentInsetAdjustmentBehavior`), native controls, blur/glass effects, storage
- [references/styling.md](references/styling.md) — StyleSheet, NativeWind/Tailwind, platform styles, theming, dark mode
- [references/animations.md](references/animations.md) — Reanimated 3: entering/exiting, shared values, gestures, scroll-driven
- [references/state-management.md](references/state-management.md) — Zustand (selectors, persist), Jotai (atoms, derived), React Query, Context
- [references/forms.md](references/forms.md) — React Hook Form + Zod: validation, multi-step, dynamic arrays
- [references/networking.md](references/networking.md) — fetch wrapper, React Query (optimistic updates), auth tokens, offline, API routes, webhooks
- [references/performance.md](references/performance.md) — Profiling workflow, FlashList + `memo`, bundle analysis, TTI, memory leaks, animation perf
- [references/testing.md](references/testing.md) — Jest, React Native Testing Library, E2E with Maestro
- [references/native-capabilities.md](references/native-capabilities.md) — Camera, location, permissions (`use*Permissions` hooks), haptics, notifications, biometrics
- [references/engineering.md](references/engineering.md) — Project layout (`components/ui/`, `stores/`, `services/`), path aliases, SDK upgrades, EAS build/submit, CI/CD, DOM components

## Quick Reference

### Component Preferences

| Purpose | Use | Instead of |
|---------|-----|------------|
| Lists | `FlashList` (`@shopify/flash-list`) + `memo` items | `FlatList` (no view recycling) |
| Images | `expo-image` | RN `<Image>` (no cache, no WebP) |
| Press | `Pressable` | `TouchableOpacity` (legacy) |
| Audio | `expo-audio` | `expo-av` (deprecated) |
| Video | `expo-video` | `expo-av` (deprecated) |
| Animations | Reanimated 3 | RN Animated API (limited) |
| Gestures | Gesture Handler | PanResponder (legacy) |
| Platform check | `process.env.EXPO_OS` | `Platform.OS` |
| Context | `React.use()` | `React.useContext()` (React 18) |
| Safe area scroll | `contentInsetAdjustmentBehavior="automatic"` | `<SafeAreaView>` |
| SF Symbols | `expo-image` with `source="sf:name"` | `expo-symbols` |

### Scaling Up

| Situation | Consider |
|-----------|----------|
| Long lists with scroll jank | Virtualized list libraries (e.g. FlashList) |
| Want Tailwind-style classes | NativeWind v4 |
| High-frequency storage reads | Sync-based storage (e.g. MMKV) |
| New project with Expo | Expo Router over bare React Navigation |

### State Management

| State Type | Solution |
|------------|----------|
| Local UI state | `useState` / `useReducer` |
| Shared app state | Zustand or Jotai |
| Server / async data | React Query |
| Form state | React Hook Form + Zod |

### Performance Priorities

| Priority | Issue | Fix |
|----------|-------|-----|
| CRITICAL | Long list jank | `FlashList` + memoized items |
| CRITICAL | Large bundle | Avoid barrel imports, enable R8 |
| HIGH | Too many re-renders | Zustand selectors, React Compiler |
| HIGH | Slow startup | Disable bundle compression, native nav |
| MEDIUM | Animation drops | Only animate `transform`/`opacity` |

## New Project Init

```bash
# 1. Create project
npx create-expo-app@latest my-app --template blank-typescript
cd my-app

# 2. Install Expo Router + core deps
npx expo install expo-router react-native-safe-area-context react-native-screens

# 3. (Optional) Common extras
npx expo install expo-image react-native-reanimated react-native-gesture-handler
```

Then configure:

1. Set entry point in `package.json`: `"main": "expo-router/entry"`
2. Add scheme in `app.json`: `"scheme": "my-app"`
3. Delete `App.tsx` and `index.ts`
4. Create `app/_layout.tsx` as root Stack layout
5. Create `app/(tabs)/_layout.tsx` for tab navigation
6. Create route files in `app/(tabs)/` (see [navigation.md](references/navigation.md))

For web support, also install: `npx expo install react-native-web react-dom @expo/metro-runtime`

## Core Principles

**Consult references before writing**: when implementing navigation, lists, networking, or project setup, read the matching reference file above for patterns and pitfalls.

**Try Expo Go first** (`npx expo start`). Custom builds (`eas build`) only needed when using local Expo modules, Apple targets, or third-party native modules not in Expo Go.

**Conditional rendering**: use `{count > 0 && <Text />}` not `{count && <Text />}` (renders "0").

**Animation rule**: only animate `transform` and `opacity` — GPU-composited, no layout thrash.

**Imports**: always import directly from source, not barrel files — avoids bundle bloat.

**Lists and images**: before using `FlatList` or RN `Image`, check the Component Preferences table above — `FlashList` and `expo-image` are almost always the right choice.

**Route files**: always use kebab-case, never co-locate components/types/utils in `app/`.

## Checklist

### New Project Setup
- [ ] `tsconfig.json` path aliases configured
- [ ] `EXPO_PUBLIC_API_URL` env var set per environment
- [ ] Root layout has `GestureHandlerRootView` (if using gestures)
- [ ] `contentInsetAdjustmentBehavior="automatic"` on all scroll views
- [ ] `FlashList` instead of `FlatList` for lists > 20 items

### Before Shipping
- [ ] Profile in `--profile` mode, fix frames > 16ms
- [ ] Bundle analyzed (`source-map-explorer`), no barrel imports
- [ ] R8 enabled for Android
- [ ] Unit + component tests for critical paths
- [ ] E2E flows for login, core feature, checkout

---

Flutter development → see `flutter-dev` skill.
iOS native (UIKit/SwiftUI) → see `ios-application-dev` skill.
Android native (Kotlin/Compose) → see `android-native-dev` skill.

*React Native is a trademark of Meta Platforms, Inc. Expo is a trademark of 650 Industries, Inc. All other product names are trademarks of their respective owners.*
