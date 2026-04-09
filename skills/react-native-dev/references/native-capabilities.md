# Native Capabilities Reference

Camera, location, permissions, haptics, notifications, and biometrics for Expo/React Native.

## Permissions

All Expo modules that need permissions expose a `use*Permissions()` hook. Follow this pattern:

1. Call the permission hook to get current status and a request function
2. Check `status` — if not `granted`, show a rationale and call `requestPermission()`
3. If the user denies twice, `canAskAgain` becomes `false` — direct them to Settings

```tsx
import { useCameraPermissions } from "expo-camera";

const [permission, requestPermission] = useCameraPermissions();

if (!permission?.granted) {
  // Show rationale, then call requestPermission()
}
```

| Module | Permission Hook |
|--------|----------------|
| `expo-camera` | `useCameraPermissions()` |
| `expo-location` | `useForegroundPermissions()` / `useBackgroundPermissions()` |
| `expo-media-library` | `usePermissions()` |
| `expo-notifications` | `getPermissionsAsync()` / `requestPermissionsAsync()` |
| `expo-contacts` | `usePermissions()` |

For modules without a hook, use `requestPermissionsAsync()` / `getPermissionsAsync()` directly.

## Camera

```tsx
import { CameraView, useCameraPermissions } from "expo-camera";

const [permission, requestPermission] = useCameraPermissions();
const cameraRef = useRef<CameraView>(null);

// Capture a photo
const photo = await cameraRef.current?.takePictureAsync();

// Toggle front/back
const [facing, setFacing] = useState<"front" | "back">("back");
```

For simple photo/video selection without a camera UI, use `expo-image-picker`:

```tsx
import * as ImagePicker from "expo-image-picker";

const result = await ImagePicker.launchImageLibraryAsync({
  mediaTypes: ["images"],
  allowsEditing: true,
  quality: 0.8,
});
```

## Location

```tsx
import * as Location from "expo-location";

// One-time location
const { status } = await Location.requestForegroundPermissionsAsync();
if (status === "granted") {
  const location = await Location.getCurrentPositionAsync({});
  // location.coords.latitude, location.coords.longitude
}
```

For background location tracking, request `requestBackgroundPermissionsAsync()` and register a background task. Background location requires the `location` background mode in `app.json`:

```json
{
  "expo": {
    "ios": { "infoPlist": { "UIBackgroundModes": ["location"] } }
  }
}
```

## Haptics

```tsx
import * as Haptics from "expo-haptics";

// Light tap feedback (button press)
Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

// Success / error / warning
Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

// Selection change (picker scroll)
Haptics.selectionAsync();
```

| Style | When to Use |
|-------|-------------|
| `ImpactFeedbackStyle.Light` | Button taps, toggles |
| `ImpactFeedbackStyle.Medium` | Drag snaps, significant actions |
| `ImpactFeedbackStyle.Heavy` | Destructive actions, impacts |
| `NotificationFeedbackType.Success` | Task completed |
| `NotificationFeedbackType.Warning` | Attention needed |
| `NotificationFeedbackType.Error` | Action failed |
| `selectionAsync()` | Picker/slider value changes |

## Notifications

### Push Notifications (Expo)

```tsx
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";

async function registerForPushNotifications() {
  if (!Device.isDevice) return; // Push doesn't work on simulators

  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== "granted") return;

  const token = await Notifications.getExpoPushTokenAsync({
    projectId: "your-project-id", // From app.json > extra > eas > projectId
  });
  // Send token.data to your server
}
```

### Notification Handlers

```tsx
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

// Listen for received/tapped notifications
const subscription = Notifications.addNotificationReceivedListener(notification => {
  // Notification received while app is foregrounded
});
```

## Biometrics

```tsx
import * as LocalAuthentication from "expo-local-authentication";

const hasHardware = await LocalAuthentication.hasHardwareAsync();
const isEnrolled = await LocalAuthentication.isEnrolledAsync();

if (hasHardware && isEnrolled) {
  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: "Authenticate to continue",
    fallbackLabel: "Use passcode",
  });
  if (result.success) {
    // Authenticated
  }
}
```
