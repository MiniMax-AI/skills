# Animations Reference

Reanimated 3 animations, gestures, and transitions for Expo/React Native.

## Core Rules

- **Only animate `transform` and `opacity`** — GPU-composited, no layout recalculation
- Use `useDerivedValue` for computed animated values, not inline JS expressions
- Use `Gesture.Tap` instead of `Pressable` inside `GestureDetector`
- All Reanimated callbacks run as worklets on the UI thread — no async/await

## Setup

```bash
npx expo install react-native-reanimated react-native-gesture-handler
```

```js
// babel.config.js
module.exports = { presets: ["babel-preset-expo"], plugins: ["react-native-reanimated/plugin"] };
```

```tsx
// app/_layout.tsx — wrap root in GestureHandlerRootView
import { GestureHandlerRootView } from "react-native-gesture-handler";
export default function RootLayout() {
  return <GestureHandlerRootView style={{ flex: 1 }}><Stack /></GestureHandlerRootView>;
}
```

## Entering / Exiting Animations

```tsx
import Animated, {
  FadeIn, FadeOut,
  SlideInRight, SlideOutLeft,
  ZoomIn, ZoomOut,
  BounceIn,
} from "react-native-reanimated";

// Basic
<Animated.View entering={FadeIn} exiting={FadeOut}>
  <Text>Content</Text>
</Animated.View>

// With options
<Animated.View
  entering={FadeIn.duration(300).delay(100)}
  exiting={SlideOutLeft.duration(200)}
/>

// Spring-based
<Animated.View entering={ZoomIn.springify().damping(15)} />
```

### Built-in Presets

| Category | Entering | Exiting |
|----------|----------|---------|
| Fade | `FadeIn`, `FadeInUp`, `FadeInDown`, `FadeInLeft`, `FadeInRight` | `FadeOut*` |
| Slide | `SlideInUp`, `SlideInDown`, `SlideInLeft`, `SlideInRight` | `SlideOut*` |
| Zoom | `ZoomIn`, `ZoomInUp`, `ZoomInDown` | `ZoomOut*` |
| Bounce | `BounceIn`, `BounceInUp`, `BounceInDown` | `BounceOut*` |
| Flip | `FlipInXUp`, `FlipInYLeft` | `FlipOut*` |
| Roll | `RollInLeft`, `RollInRight` | `RollOut*` |
| Stretch | `StretchInX`, `StretchInY` | `StretchOut*` |
| Pinwheel | `PinwheelIn` | `PinwheelOut` |
| Rotate | `RotateInDownLeft` | `RotateOut*` |
| LightSpeed | `LightSpeedInLeft` | `LightSpeedOut*` |

## Shared Values & useAnimatedStyle

```tsx
import {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  withRepeat,
  withSequence,
  Easing,
} from "react-native-reanimated";

const offset = useSharedValue(0);
const opacity = useSharedValue(1);

const animStyle = useAnimatedStyle(() => ({
  transform: [{ translateX: offset.value }],
  opacity: opacity.value,
}));

// Animate
offset.value = withSpring(100);
opacity.value = withTiming(0, { duration: 300, easing: Easing.out(Easing.quad) });

// Repeat
opacity.value = withRepeat(withTiming(0.3, { duration: 800 }), -1, true);

// Sequence
offset.value = withSequence(
  withTiming(-10, { duration: 100 }),
  withTiming(10, { duration: 100 }),
  withSpring(0),
);

<Animated.View style={animStyle} />
```

## useDerivedValue

```tsx
import { useDerivedValue } from "react-native-reanimated";

const progress = useSharedValue(0); // 0–1
const rotation = useDerivedValue(() => `${progress.value * 360}deg`);
const scale = useDerivedValue(() => 0.5 + progress.value * 0.5);

const animStyle = useAnimatedStyle(() => ({
  transform: [{ rotate: rotation.value }, { scale: scale.value }],
}));
```

## Layout Animations

```tsx
import { Layout, LinearTransition, CurvedTransition } from "react-native-reanimated";

// Item reorder/add/remove animation
<Animated.View layout={LinearTransition}>
  {/* Content that changes size/position */}
</Animated.View>

// Spring layout transition
<Animated.View layout={LinearTransition.springify()}>
```

## Gestures

```tsx
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import { useSharedValue, useAnimatedStyle, withSpring } from "react-native-reanimated";

// Pan gesture
const offsetX = useSharedValue(0);
const offsetY = useSharedValue(0);

const panGesture = Gesture.Pan()
  .onUpdate((e) => {
    offsetX.value = e.translationX;
    offsetY.value = e.translationY;
  })
  .onEnd(() => {
    offsetX.value = withSpring(0);
    offsetY.value = withSpring(0);
  });

const animStyle = useAnimatedStyle(() => ({
  transform: [{ translateX: offsetX.value }, { translateY: offsetY.value }],
}));

<GestureDetector gesture={panGesture}>
  <Animated.View style={animStyle} />
</GestureDetector>
```

```tsx
// Tap gesture (use instead of Pressable inside GestureDetector)
const tapGesture = Gesture.Tap()
  .numberOfTaps(1)
  .onEnd(() => {
    scale.value = withSequence(withTiming(0.95), withSpring(1));
  });

// Pinch gesture
const baseScale = useSharedValue(1);
const savedScale = useSharedValue(1);

const pinchGesture = Gesture.Pinch()
  .onUpdate((e) => { baseScale.value = savedScale.value * e.scale; })
  .onEnd(() => { savedScale.value = baseScale.value; });

// Composed gestures
const composed = Gesture.Simultaneous(panGesture, pinchGesture);
const exclusive = Gesture.Exclusive(tapGesture, panGesture);
```

## Scroll-Driven Animations

```tsx
import Animated, {
  useAnimatedScrollHandler,
  useSharedValue,
  interpolate,
  Extrapolation,
} from "react-native-reanimated";

const scrollY = useSharedValue(0);
const scrollHandler = useAnimatedScrollHandler((e) => {
  scrollY.value = e.contentOffset.y;
});

// Parallax header
const headerStyle = useAnimatedStyle(() => ({
  transform: [{
    translateY: interpolate(scrollY.value, [0, 200], [0, -100], Extrapolation.CLAMP),
  }],
  opacity: interpolate(scrollY.value, [0, 200], [1, 0], Extrapolation.CLAMP),
}));

<Animated.ScrollView onScroll={scrollHandler} scrollEventThrottle={16}>
  <Animated.View style={headerStyle}>
    <Text>Parallax Header</Text>
  </Animated.View>
</Animated.ScrollView>
```

## Zoom Transitions (Expo Router, iOS 18+)

```tsx
import { Link } from "expo-router";

<Link href="/detail" asChild>
  <Link.AppleZoom>
    <Pressable>
      <Image source={thumbnail} />
    </Pressable>
  </Link.AppleZoom>
</Link>
```

## Adding Animations to State Changes

```tsx
// ✓ Always add entering/exiting for state-driven UI changes
{isVisible && (
  <Animated.View entering={FadeIn.duration(200)} exiting={FadeOut.duration(150)}>
    <Toast message={message} />
  </Animated.View>
)}

// ✓ AnimatedFlatList for list item changes
import Animated from "react-native-reanimated";
const AnimatedFlashList = Animated.createAnimatedComponent(FlashList);
```

## Common Mistakes

| Wrong | Right |
|-------|-------|
| Animate `width`/`height` | Animate `transform: scaleX/scaleY` |
| Inline JS math in `useAnimatedStyle` | `useDerivedValue` for computations |
| `Pressable` inside `GestureDetector` | `Gesture.Tap()` |
| `async` in worklet | Run async outside, update sharedValue in callback |
| Frequent `console.log` in worklet | `console.log` works but serializes to JS thread — use sparingly in hot paths |
