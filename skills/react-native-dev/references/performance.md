# Performance Reference

Diagnosing and fixing performance issues in React Native / Expo apps.

## Profiling Workflow

Before optimizing, identify the actual bottleneck:

1. **JS thread** — Open React Native DevTools (press `j` in Metro terminal) → Profiler tab → record interaction → look for components with long render times
2. **Native thread** — iOS: Xcode Instruments (Time Profiler); Android: Android Studio CPU Profiler
3. **Measure, don't guess** — Always reproduce the issue in a release-like build (`npx expo run:ios --configuration Release`)

## Rendering

### Virtualized Lists

Never render large datasets inside a `ScrollView`. Use a virtualized list that recycles off-screen views:

```tsx
import { FlashList } from "@shopify/flash-list";

function ProductCatalog({ products }: { products: Product[] }) {
  return (
    <FlashList
      data={products}
      renderItem={({ item }) => <ProductRow product={item} />}
      estimatedItemSize={72}
      keyExtractor={(p) => p.sku}
    />
  );
}

const ProductRow = memo(function ProductRow({ product }: { product: Product }) {
  return (
    <View style={rowStyles.container}>
      <Image source={product.thumbnail} style={rowStyles.image} />
      <Text style={rowStyles.title}>{product.name}</Text>
    </View>
  );
});
```

Key points:
- Wrap list items with `memo` to skip re-renders when props haven't changed
- Always provide `estimatedItemSize` — FlashList uses it for layout estimation
- Extract `renderItem` or use a named component to keep stable references

### Minimizing Re-renders

**Split state by concern.** A single large state object forces every subscriber to re-render on any change:

```tsx
// Zustand — select only the slice you need
const count = useStore((s) => s.cart.itemCount);

// Jotai — one atom per concern
const cartTotalAtom = atom((get) => {
  const items = get(cartItemsAtom);
  return items.reduce((sum, i) => sum + i.price * i.qty, 0);
});
```

**React Compiler** (Expo SDK 54+) automatically memoizes components and hooks. Enable it to eliminate most manual `useMemo`/`useCallback`:

```json
// app.json
{ "expo": { "experiments": { "reactCompiler": true } } }
```

### Deferred Updates

When a state change triggers expensive computation (filtering a long list, rendering a complex tree), defer the update so typing or scrolling stays responsive:

```tsx
const [search, setSearch] = useState("");
const deferred = useDeferredValue(search);

const results = useMemo(
  () => catalog.filter((p) => p.name.toLowerCase().includes(deferred.toLowerCase())),
  [catalog, deferred],
);
```

### TextInput on Android

Controlled `TextInput` (with `value` + `onChangeText`) can lag on Android because every keystroke round-trips through the JS thread. For search bars or other high-frequency inputs, prefer uncontrolled mode:

```tsx
const ref = useRef<TextInput>(null);

<TextInput
  ref={ref}
  defaultValue=""
  onEndEditing={(e) => handleSearch(e.nativeEvent.text)}
/>
```

## Startup Time (TTI)

### Measuring

```tsx
import { PerformanceObserver, performance } from "react-native-performance";

performance.mark("nativeLaunch");

export default function App() {
  useEffect(() => {
    performance.measure("TTI", "nativeLaunch");
  }, []);
  // ...
}
```

Always measure **cold starts** — kill the app completely before each measurement.

### Reducing TTI

- **Android bundle mmap** — Set `expo.useLegacyPackaging=false` in `android/gradle.properties` so Hermes memory-maps the bundle instead of decompressing it
- **Preload heavy routes** — Call `preloadRouteAsync("/dashboard")` (from `expo-router`) while the user is still on the splash/login screen
- **Lazy-load non-critical screens** — Screens behind deep navigation don't need to be in the initial bundle

## Bundle & App Size

### Inspecting the Bundle

```bash
npx expo export --platform ios --source-maps --output-dir dist
npx source-map-explorer dist/bundles/ios/*.js
```

Common wins:
- **Direct imports** — `import groupBy from "lodash/groupBy"` instead of `import { groupBy } from "lodash"`
- **Remove dead Intl polyfills** — Hermes ships with built-in `Intl` support since SDK 50
- **Tree shaking** — Enable via `"experiments": { "treeShaking": true }` in app config (SDK 52+)

### Shrinking the Native Binary

```properties
# android/gradle.properties
android.enableProguardInReleaseBuilds=true
```

Inspect the final artifact:
- iOS: download the `.ipa` from EAS, unzip, check `Payload/*.app` size
- Android: open the `.aab`/`.apk` in Android Studio → Build → Analyze APK

## Memory

### Preventing Leaks

Every subscription, listener, or long-lived resource acquired in `useEffect` must be cleaned up:

```tsx
useEffect(() => {
  const sub = AppState.addEventListener("change", onAppStateChange);
  return () => sub.remove();
}, []);
```

For fetch calls, pass an `AbortSignal` and abort on unmount:

```tsx
useEffect(() => {
  const ac = new AbortController();
  loadProducts(ac.signal);
  return () => ac.abort();
}, [categoryId]);
```

### Native Memory

- Monitor with Xcode Memory Graph Debugger (iOS) or Android Studio Memory Profiler
- Release heavy native resources (camera sessions, audio players) in cleanup
- In Swift/Kotlin modules, watch for retain cycles — use `[weak self]` / `WeakReference`

## Animations

Only animate **`transform`** and **`opacity`**. These properties are composited on the GPU and don't trigger layout recalculation:

```tsx
const style = useAnimatedStyle(() => ({
  opacity: withTiming(visible.value ? 1 : 0),
  transform: [{ translateY: withSpring(offset.value) }],
}));
```

Animating `width`, `height`, `margin`, `padding`, or `top`/`left` forces the layout engine to re-measure on every frame — a common source of dropped frames.

Keep gesture callbacks on the UI thread:

```tsx
const drag = Gesture.Pan().onUpdate((e) => {
  "worklet";
  translateX.value = e.translationX;
});
```

## Native Module Performance

- Prefer **async** Turbo Module methods — synchronous calls block the JS thread
- Use native SDK implementations over JS polyfills (`expo-crypto` over `crypto-js`, `react-native-mmkv` over AsyncStorage for hot paths)
- **Android 16KB page alignment** is required for Google Play (2025+). Verify third-party `.so` files are compiled with 16KB alignment

## Troubleshooting Guide

| Symptom | Where to Look | Likely Fix |
|---------|--------------|------------|
| Scroll jank in long lists | JS thread — re-renders | Virtualized list + memoized items |
| Typing lag in search bar | JS thread — controlled input | Uncontrolled `TextInput` with `defaultValue` |
| Slow cold start | Bundle size, sync init | Mmap bundle, preload routes, lazy screens |
| App binary too large | Native assets, unused libs | R8 (Android), analyze bundle, direct imports |
| Growing memory over time | Effect cleanup | Return teardown from every `useEffect` |
| Choppy enter/exit animation | Animated properties | Only `transform` + `opacity`, use worklets |
| Re-renders cascade across app | Global state shape | Atomic selectors (Zustand/Jotai), React Compiler |
