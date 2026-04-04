# Styling Reference

StyleSheet, NativeWind/Tailwind, platform-specific styles, and theming for Expo/React Native.

## StyleSheet

```tsx
import { StyleSheet } from "react-native";
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  text: { fontSize: 16, fontWeight: "600" },
});
```

Prefer `StyleSheet.create` over inline style objects — it validates styles at creation time and enables potential future optimizations.

## Platform-Specific Styles

```tsx
import { Platform, StyleSheet } from "react-native";

const styles = StyleSheet.create({
  shadow: Platform.select({
    ios: { shadowColor: "#000", shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4 },
    android: { elevation: 4 },
  }),
});
```

Since React Native 0.76+, `boxShadow` is supported as a unified cross-platform shadow API. Prefer it over platform-specific shadow properties when targeting New Architecture.

## NativeWind / Tailwind CSS

For existing projects, check which NativeWind version is in `package.json` and follow the corresponding docs. For new projects, use NativeWind v4 (stable).

### Installation (NativeWind v4)

```bash
npx expo install nativewind tailwindcss@3 \
  tailwind-merge clsx
```

### Configuration

```js
// babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],
    plugins: ["nativewind/babel"],
  };
};
```

```js
// tailwind.config.js
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: { extend: {} },
};
```

```css
/* global.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

```tsx
// app/_layout.tsx
import "../global.css";
```

### Usage

```tsx
<View className="flex-1 bg-white p-4">
  <Text className="text-lg font-semibold text-gray-900">Title</Text>
  <Pressable className="mt-4 rounded-lg bg-blue-500 px-4 py-2">
    <Text className="text-center text-white font-medium">Button</Text>
  </Pressable>
</View>
```

### Conditional Classes

```tsx
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

<View className={cn("p-4", isActive && "bg-blue-500", isDisabled && "opacity-50")} />
```

## Theming and Dark Mode

For apps using NativeWind, use Tailwind's `dark:` variant:

```tsx
<View className="bg-white dark:bg-gray-900">
  <Text className="text-gray-900 dark:text-white">Adaptive text</Text>
</View>
```

For StyleSheet-based projects, read the system color scheme and map it to a theme object:

```tsx
import { useColorScheme } from "react-native";

const colorScheme = useColorScheme(); // "light" | "dark"
```

Keep color tokens in a central `constants/colors.ts` file with light and dark variants. Pass the active palette via React Context or a Zustand store.
