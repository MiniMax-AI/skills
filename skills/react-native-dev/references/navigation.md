# Navigation Reference

Expo Router file-based navigation: Stack, Tabs, modals, links, and context menus.

## File Conventions

```
app/
  _layout.tsx              Root layout (providers, NativeTabs)
  index.tsx                → /
  about.tsx                → /about
  user/
    [id].tsx               → /user/:id
    [id]/
      posts.tsx            → /user/:id/posts
  (tabs)/
    _layout.tsx            Tab navigator (group, not in URL)
    home.tsx               → /home
    profile.tsx            → /profile
  (index,search)/
    _layout.tsx            Shared Stack for both tabs
    index.tsx              → /
    search.tsx             → /search
    i/[id].tsx             → /i/:id (shared detail screen)
  api/
    users+api.ts           → /api/users (server route)
```

**Rules**:
- Routes live only in `app/` — never co-locate components, types, or utils there
- Always have a route matching `/` (may be inside a group)
- Remove old route files when restructuring navigation
- Use kebab-case filenames

## Root Layout (Stack)

```tsx
// app/_layout.tsx — root is always a Stack
import { Stack } from "expo-router";

export default function RootLayout() {
  return (
    <Stack
      screenOptions={{
        headerTransparent: true,
        headerLargeTitle: true,
        headerBackButtonDisplayMode: "minimal",
      }}
    >
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="user/[id]" options={{ headerLargeTitle: false }} />
    </Stack>
  );
}
```

**Always set page title via `Stack.Screen options.title`**, never use a custom Text element as a title.

## Tabs — Which to Use

| Scenario | Use |
|----------|-----|
| Custom design system, cross-platform | **JS Tabs** (stable, fully customizable) |
| iOS-native look, Liquid Glass (iOS 26+) | **NativeTabs** (alpha, limited customization) |

## JS Tabs

```tsx
// app/(tabs)/_layout.tsx
import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

export default function TabLayout() {
  return (
    <Tabs screenOptions={{ tabBarActiveTintColor: "blue" }}>
      <Tabs.Screen
        name="home"
        options={{
          tabBarLabel: "Home",
          tabBarIcon: ({ color, size }) => <Ionicons name="home" color={color} size={size} />,
        }}
      />
    </Tabs>
  );
}
```

## NativeTabs (alpha, iOS 18+)

> Alpha API — all tabs render at once, limited customization, max 5 tabs on Android. Use when you want native iOS look (Liquid Glass, native blur/transitions) without rebuilding it yourself.

```tsx
import { NativeTabs } from "expo-router/unstable-native-tabs";

export default function Layout() {
  return (
    <NativeTabs>
      <NativeTabs.Trigger name="(index)">
        <NativeTabs.Trigger.Icon sf="house" />
        <NativeTabs.Trigger.Label>Home</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="(profile)">
        <NativeTabs.Trigger.Icon sf="person" />
        <NativeTabs.Trigger.Label>Profile</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
```

## Shared Stack for Multiple Tabs

```tsx
// app/(index,search)/_layout.tsx — shared Stack for both index and search tabs
import { Stack } from "expo-router/stack";

const tabLabels: Record<string, string> = { index: "Home", search: "Explore" };

export default function Layout({ segment }: { segment: string }) {
  const activeTab = segment.replace(/[()]/g, "");

  return (
    <Stack screenOptions={{ headerLargeTitle: true, headerBackButtonDisplayMode: "minimal" }}>
      <Stack.Screen name={activeTab} options={{ title: tabLabels[activeTab] }} />
      <Stack.Screen name="i/[id]" options={{ headerLargeTitle: false }} />
    </Stack>
  );
}
```

## Link Component

```tsx
import { Link } from "expo-router";

// Basic navigation
<Link href="/about">About</Link>

// Dynamic routes
<Link href={`/user/${userId}`}>Profile</Link>

// Wrapping custom component
<Link href="/settings" asChild>
  <Pressable><Text>Settings</Text></Pressable>
</Link>
```

## Programmatic Navigation

```tsx
import { useRouter, useLocalSearchParams } from "expo-router";

const router = useRouter();
router.push("/settings");
router.replace("/login");   // No back button
router.back();

// Access route params
const { id } = useLocalSearchParams<{ id: string }>();
```

## Modals & Sheets

```tsx
// Modal presentation
<Stack.Screen options={{ presentation: "modal" }} />

// Form sheet with detents
<Stack.Screen
  options={{
    presentation: "formSheet",
    sheetGrabberVisible: true,
    sheetAllowedDetents: [0.5, 1.0],
    contentStyle: { backgroundColor: "transparent" }, // Liquid glass on iOS 26+
  }}
/>
```

## Context Menus on Links

```tsx
<Link href="/settings" asChild>
  <Link.Trigger>
    <Pressable><Card /></Pressable>
  </Link.Trigger>
  <Link.Menu>
    <Link.MenuAction
      title="Share"
      icon="square.and.arrow.up"
      onPress={handleShare}
    />
    <Link.MenuAction
      title="Delete"
      icon="trash"
      destructive
      onPress={handleDelete}
    />
    <Link.Menu title="More" icon="ellipsis">
      <Link.MenuAction title="Copy" icon="doc.on.doc" onPress={() => {}} />
    </Link.Menu>
  </Link.Menu>
</Link>
```

## Link Previews (iOS only, requires Expo SDK 54+)

```tsx
<Link href="/detail">
  <Link.Trigger>
    <Pressable><Card /></Pressable>
  </Link.Trigger>
  <Link.Preview />  {/* Shows peek preview on 3D touch / long press */}
</Link>
```

## Header Search Bar

```tsx
// In Stack.Screen — preferred over building custom search UI
<Stack.Screen
  options={{
    headerSearchBarOptions: {
      placeholder: "Search...",
      onChangeText: (e) => setQuery(e.nativeEvent.text),
      onCancelButtonPress: () => setQuery(""),
    },
  }}
/>
```

## Deep Linking

```json
// app.json
{
  "expo": {
    "scheme": "myapp",
    "ios": {
      "associatedDomains": ["applinks:myapp.example.com"]
    },
    "android": {
      "intentFilters": [
        {
          "action": "VIEW",
          "autoVerify": true,
          "data": [{ "scheme": "https", "host": "myapp.example.com" }],
          "category": ["BROWSABLE", "DEFAULT"]
        }
      ]
    }
  }
}
```

Expo Router handles deep links automatically — `/user/123` maps to `app/user/[id].tsx`.

## ScrollView in Routes

When a route belongs to a Stack, its first child should almost always be a ScrollView:

```tsx
export default function HomeScreen() {
  return (
    <ScrollView contentInsetAdjustmentBehavior="automatic">
      {/* Content */}
    </ScrollView>
  );
}
```

Use `contentInsetAdjustmentBehavior="automatic"` on `ScrollView`, `FlatList`, and `SectionList` — this handles safe areas and header insets automatically. Prefer it over `<SafeAreaView>`.
