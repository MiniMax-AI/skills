# SwiftUI Design Guidelines

Design rules based on Apple Human Interface Guidelines for building native iOS interfaces with SwiftUI.

---

## Design Philosophy

iOS design prioritizes **content over chrome**. The interface should feel invisible—users focus on their tasks, not the UI.

**Key mindsets:**

1. **Let content breathe** — Use full-screen layouts, minimize borders and boxes, let images and text take center stage

2. **Leverage system conventions** — Users already know how iOS works; don't reinvent navigation, gestures, or controls

3. **Design for fingers** — Touch is imprecise; generous tap targets and forgiving gesture recognition matter more than pixel-perfect layouts

4. **Respect user choices** — Honor Dynamic Type, Dark Mode, Reduce Motion, and other accessibility settings as first-class requirements

**iOS 26+ Liquid Glass:**
The latest iOS introduces translucent UI elements that respond to lighting and content behind them. Typography is bolder, text tends left-aligned for easier scanning.

---

## 1. Layout & Safe Areas

**Impact:** CRITICAL

### 1.1 Minimum 44pt Touch Targets

All interactive elements must have minimum 44x44 **points** (not pixels—points scale with screen density).

```swift
Button(action: handleTap) {
    Image(systemName: "heart.fill")
}
.frame(minWidth: 44, minHeight: 44)
```

Avoid placing critical interactions near screen edges where system gestures operate.

### 1.2 Respect Safe Areas

Never place interactive or essential content under the status bar, Dynamic Island, or home indicator. SwiftUI respects safe areas by default. Use `.ignoresSafeArea()` only for background fills, images, or decorative elements—never for text or interactive controls.

```swift
ZStack {
    LinearGradient(colors: [.blue, .purple], startPoint: .top, endPoint: .bottom)
        .ignoresSafeArea()
    
    VStack {
        Text("Welcome")
            .font(.largeTitle)
        Button("Get Started") { }
    }
}
```

### 1.3 Primary Actions in Thumb Zone

Place primary actions at the bottom of the screen where the user's thumb naturally rests. Secondary actions and navigation belong at the top.

```swift
VStack {
    ScrollView {
        // Content
    }
    
    Spacer()
    
    Button("Submit") { submit() }
        .buttonStyle(.borderedProminent)
        .padding(.horizontal)
        .padding(.bottom)
}
```

### 1.4 Support All Screen Sizes

Design for iPhone SE (375pt) through iPad Pro (1024pt+). Use Size Classes to adapt:

```swift
@Environment(\.horizontalSizeClass) private var sizeClass

var body: some View {
    if sizeClass == .compact {
        VStack { content }
    } else {
        HStack { content }
    }
}
```

| Size Class | Devices |
|------------|---------|
| Compact width | iPhone portrait, small iPhone landscape |
| Regular width | iPad, large iPhone landscape |

Use flexible layouts, avoid hardcoded widths:

```swift
HStack(spacing: 16) {
    ForEach(categories) { category in
        CategoryCard(category: category)
            .frame(maxWidth: .infinity)
    }
}
```

### 1.5 8pt Grid Alignment

Align spacing, padding, and element sizes to multiples of 8 points (8, 16, 24, 32, 40, 48). Use 4pt for fine adjustments.

### 1.6 Landscape Support

Support landscape orientation unless the app is task-specific (e.g., camera). Use `ViewThatFits` or `GeometryReader` for adaptive layouts.

```swift
ViewThatFits {
    HStack { contentViews }
    VStack { contentViews }
}
```

---

## 2. Navigation

**Impact:** CRITICAL

### 2.1 Tab Bar for Top-Level Sections

Use a tab bar at the bottom of the screen for 3 to 5 top-level sections. Each tab should represent a distinct category of content or functionality.

```swift
TabView(selection: $selectedTab) {
    HomeView()
        .tabItem {
            Label("Home", systemImage: "house")
        }
        .tag(Tab.home)
    
    DiscoverView()
        .tabItem {
            Label("Discover", systemImage: "magnifyingglass")
        }
        .tag(Tab.discover)
    
    AccountView()
        .tabItem {
            Label("Account", systemImage: "person")
        }
        .tag(Tab.account)
}
```

### 2.2 Navigation Architecture

**Tab Bar (Flat)** — For 3-5 equal-importance sections
- Always visible except when covered by modals
- Each tab maintains its own navigation stack
- Most important content leftmost (easier thumb access)

**Hierarchical (Drill-Down)** — For tree-structured info
- Push/pop navigation with back button
- Minimize depth (3-4 levels max)
- Provide search as escape hatch for deep trees

**Modal (Focused Tasks)** — For self-contained workflows
- Full-screen for critical tasks
- Page sheet for dismissible tasks (swipe-down)
- Clear Done/Cancel with confirmation if data loss possible

Never use hamburger menus—they reduce feature discoverability significantly.

### 2.3 Large Titles in Primary Views

Use `.navigationBarTitleDisplayMode(.large)` for top-level views. Titles transition to inline when the user scrolls.

```swift
NavigationStack {
    List(conversations) { conversation in
        ConversationRow(conversation: conversation)
    }
    .navigationTitle("Inbox")
    .navigationBarTitleDisplayMode(.large)
}
```

### 2.4 Never Override Back Swipe

The swipe-from-left-edge gesture for back navigation is a system-level expectation. Never attach custom gesture recognizers that interfere with it.

### 2.5 Use NavigationStack for Hierarchical Content

Use `NavigationStack` (not the deprecated `NavigationView`) for drill-down content. Use `NavigationPath` for programmatic navigation.

```swift
@State private var navPath = NavigationPath()

NavigationStack(path: $navPath) {
    List(products) { product in
        NavigationLink(value: product) {
            ProductRow(product: product)
        }
    }
    .navigationDestination(for: Product.self) { product in
        ProductDetailView(product: product)
    }
}
```

### 2.6 Preserve State Across Navigation

When users navigate back and then forward, or switch tabs, restore the previous scroll position and input state.

```swift
@SceneStorage("selectedTab") private var selectedTab = Tab.home
@SceneStorage("scrollPosition") private var scrollPosition: String?
```

---

## 3. Typography & Dynamic Type

**Impact:** HIGH

### 3.1 Use Built-in Text Styles

Always use semantic text styles—they scale with Dynamic Type automatically:

| Style | Usage |
|-------|-------|
| `.largeTitle` | Screen titles |
| `.title`, `.title2`, `.title3` | Section headers |
| `.headline` | Emphasized body text |
| `.body` | Primary content (17pt default) |
| `.callout` | Secondary emphasized |
| `.subheadline` | Supporting labels |
| `.footnote`, `.caption` | Tertiary info |
| `.caption2` | Minimum size (11pt) |

```swift
VStack(alignment: .leading, spacing: 8) {
    Text("Article Title")
        .font(.headline)
    
    Text("Published by Author Name")
        .font(.subheadline)
        .foregroundStyle(.secondary)
    
    Text(articleBody)
        .font(.body)
}
```

### 3.2 Support Dynamic Type Including Accessibility Sizes

Dynamic Type can scale text up to approximately 200% at the largest accessibility sizes. Layouts must reflow—never truncate or clip essential text.

```swift
@Environment(\.dynamicTypeSize) private var typeSize

var body: some View {
    if typeSize.isAccessibilitySize {
        VStack(alignment: .leading) { content }
    } else {
        HStack { content }
    }
}
```

### 3.3 Custom Fonts Must Scale

If you use a custom typeface, scale it with `Font.custom(_:size:relativeTo:)` so it responds to Dynamic Type.

```swift
Text("Brand Text")
    .font(.custom("Avenir-Medium", size: 17, relativeTo: .body))
```

### 3.4 SF Pro as System Font

Use the system font (SF Pro) unless brand requirements dictate otherwise. SF Pro is optimized for legibility on Apple displays.

### 3.5 Minimum 11pt Text

Never display text smaller than 11pt. Prefer 17pt for body text. Use the `caption2` style (11pt) as the absolute minimum.

### 3.6 Hierarchy Through Weight and Size

Establish visual hierarchy through font weight and size. Do not rely solely on color to differentiate text levels.

### 3.7 SF Symbols

Use SF Symbols (6,900+ icons) instead of custom image assets:

```swift
// Basic usage with automatic text alignment
Label("Favorites", systemImage: "star.fill")

// Rendering modes
Image(systemName: "cloud.sun.rain")
    .symbolRenderingMode(.hierarchical)  // or .multicolor, .palette
    .imageScale(.large)  // .small, .medium, .large
```

SF Symbols automatically match text weight, scale with Dynamic Type, and align to text baselines. Let them size naturally—don't force them into fixed-dimension containers.

---

## 4. Color & Dark Mode

**Impact:** HIGH

### 4.1 Use Semantic System Colors

Never use hard-coded RGB, hex, or `.black`/`.white` directly. Use semantic colors:

**Labels:**
- `.primary`, `.secondary`, `.tertiary`, `.quaternary`

**Backgrounds:**
- `Color(.systemBackground)` — primary surface
- `Color(.secondarySystemBackground)` — cards, grouped
- `Color(.tertiarySystemBackground)` — nested elements

**System Colors (adapt to appearance):**
- `.blue`, `.red`, `.green`, `.orange`, `.yellow`, `.purple`, `.pink`, `.cyan`, `.mint`, `.teal`, `.indigo`, `.brown`, `.gray`

```swift
VStack {
    Text("Primary content")
        .foregroundStyle(.primary)
    
    Text("Supporting info")
        .foregroundStyle(.secondary)
}
.background(Color(.systemBackground))
```

### 4.2 Custom Colors Need 4 Variants

For custom colors, define in asset catalog with all appearance combinations:
1. Light mode
2. Dark mode
3. Light mode + High Contrast
4. Dark mode + High Contrast

```swift
Text("Branded element")
    .foregroundStyle(Color("AccentBrand"))
```

For dynamic colors in code:

```swift
let dynamicColor = UIColor { traits in
    traits.userInterfaceStyle == .dark 
        ? UIColor(red: 0.9, green: 0.9, blue: 1.0, alpha: 1.0)
        : UIColor(red: 0.1, green: 0.1, blue: 0.2, alpha: 1.0)
}
```

### 4.3 Never Rely on Color Alone

Always pair color with text, icons, or shapes to convey meaning. Approximately 8% of men have some form of color vision deficiency.

```swift
HStack(spacing: 6) {
    Image(systemName: "exclamationmark.triangle.fill")
    Text("Connection failed")
}
.foregroundStyle(.red)
```

### 4.4 4.5:1 Contrast Ratio Minimum

All text must meet WCAG AA contrast ratios: 4.5:1 for normal text, 3:1 for large text (18pt+ or 14pt+ bold).

### 4.5 Support Display P3 Wide Gamut

Use Display P3 color space for vibrant, accurate colors on modern iPhones. Define colors in the asset catalog with the Display P3 gamut.

### 4.6 Background Hierarchy

Layer backgrounds to create visual depth:

```swift
// Level 1: Main view background
Color(.systemBackground)

// Level 2: Cards, grouped sections
Color(.secondarySystemBackground)

// Level 3: Nested elements within cards
Color(.tertiarySystemBackground)
```

### 4.7 One Accent Color for Interactive Elements

Choose a single tint/accent color for all interactive elements (buttons, links, toggles). This creates a consistent, learnable visual language.

```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .tint(.orange)
        }
    }
}
```

---

## 5. Accessibility

**Impact:** CRITICAL

### 5.1 VoiceOver Labels on All Interactive Elements

Every button, control, and interactive element must have a meaningful accessibility label.

```swift
Button(action: toggleFavorite) {
    Image(systemName: isFavorite ? "heart.fill" : "heart")
}
.accessibilityLabel(isFavorite ? "Remove from favorites" : "Add to favorites")
```

### 5.2 Logical VoiceOver Navigation Order

Ensure VoiceOver reads elements in a logical order. Use `.accessibilitySortPriority()` to adjust when the visual layout doesn't match the reading order.

```swift
HStack {
    Text("$49.99")
        .accessibilitySortPriority(2)
    Text("Premium Plan")
        .accessibilitySortPriority(1)
}
```

### 5.3 Support Bold Text

When the user enables Bold Text in Settings, SwiftUI text styles handle this automatically. Custom text must respond to `UIAccessibility.isBoldTextEnabled`.

### 5.4 Support Reduce Motion

Disable decorative animations and parallax when Reduce Motion is enabled.

```swift
@Environment(\.accessibilityReduceMotion) private var reduceMotion

var body: some View {
    CardView()
        .animation(reduceMotion ? nil : .spring(duration: 0.4), value: expanded)
}
```

### 5.5 Support Increase Contrast

When the user enables Increase Contrast, ensure custom colors have higher-contrast variants. Use `@Environment(\.colorSchemeContrast)` to detect.

### 5.6 Don't Convey Info Only by Color, Shape, or Position

Information must be available through multiple channels. Pair visual indicators with text or accessibility descriptions.

### 5.7 Alternative Interactions for All Gestures

Every custom gesture must have an equivalent tap-based or menu-based alternative for users who cannot perform complex gestures.

### 5.8 Support Switch Control and Full Keyboard Access

Ensure all interactions work with Switch Control (external switches) and Full Keyboard Access (Bluetooth keyboards). Test navigation order and focus behavior.

---

## 6. Gestures & Input

**Impact:** HIGH

### 6.1 Use Standard Gestures

Stick to gestures users already know:

- **Tap** — Select items, trigger buttons
- **Long press** — Show context menus, enter edit mode
- **Horizontal swipe** — List row actions (delete/archive), back navigation
- **Vertical swipe** — Scroll content, dismiss sheets
- **Pinch** — Scale images/maps
- **Rotate** — Adjust angle (photos, maps)

### 6.2 Never Override System Gestures

iOS reserves these edge gestures—do not intercept:

- Left edge swipe → back navigation
- Top-left pull → Notification Center
- Top-right pull → Control Center
- Bottom edge swipe → home/app switcher

### 6.3 Custom Gestures Must Be Discoverable

If you add a custom gesture, provide visual hints (e.g., a grabber handle) and ensure the action is also available through a visible button or menu item.

### 6.4 Support All Input Methods

Design for touch first, but also support hardware keyboards, assistive devices (Switch Control, head tracking), and pointer input.

---

## 7. Components

**Impact:** HIGH

### 7.1 Button Styles

Use the built-in button styles appropriately:

```swift
VStack(spacing: 16) {
    Button("Checkout") { checkout() }
        .buttonStyle(.borderedProminent)
    
    Button("Add to Wishlist") { addToWishlist() }
        .buttonStyle(.bordered)
    
    Button("Remove Item", role: .destructive) { removeItem() }
}
```

### 7.2 Alerts — Critical Info Only

Use alerts sparingly for critical information that requires a decision. Prefer 2 buttons; maximum 3.

```swift
.alert("Discard Draft?", isPresented: $showDiscardAlert) {
    Button("Discard", role: .destructive) { discardDraft() }
    Button("Keep Editing", role: .cancel) { }
} message: {
    Text("Your unsaved changes will be lost.")
}
```

### 7.3 Sheets for Scoped Tasks

Present sheets for self-contained tasks. Always provide a way to dismiss (close button or swipe down).

```swift
.sheet(isPresented: $showEditor) {
    NavigationStack {
        EditorView()
            .navigationTitle("Edit Profile")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showEditor = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { saveProfile() }
                }
            }
    }
    .presentationDetents([.medium, .large])
    .presentationDragIndicator(.visible)
}
```

### 7.4 Lists — The Foundation of iOS Apps

Most iOS apps are lists ("90% of mobile design is list design").

**List Styles:**
- `.insetGrouped` — Modern default (rounded corners, margins)
- `.grouped` — Traditional grouped sections
- `.plain` — Edge-to-edge rows
- `.sidebar` — Three-column iPad layout

**Swipe Actions:**
- Leading swipe → Positive actions (mark read, archive)
- Trailing swipe → Destructive actions (delete at far right)
- Maximum 3-4 actions per side

**Row Accessories:**
- Chevron → Indicates navigation
- Checkmark → Shows selection
- Detail button → Additional info without navigation

```swift
List {
    Section("Notifications") {
        ForEach(notifications) { notification in
            NotificationRow(notification: notification)
                .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                    Button(role: .destructive) {
                        delete(notification)
                    } label: {
                        Label("Delete", systemImage: "trash")
                    }
                    
                    Button {
                        markRead(notification)
                    } label: {
                        Label("Read", systemImage: "envelope.open")
                    }
                    .tint(.blue)
                }
                .swipeActions(edge: .leading) {
                    Button {
                        pin(notification)
                    } label: {
                        Label("Pin", systemImage: "pin")
                    }
                    .tint(.orange)
                }
        }
    }
}
.listStyle(.insetGrouped)
```

### 7.5 Tab Bar Behavior

- Use SF Symbols for tab icons — filled variant for the selected tab, outline for unselected
- Never hide the tab bar when navigating deeper within a tab
- Badge important counts with `.badge()`

```swift
NotificationsView()
    .tabItem {
        Label("Notifications", systemImage: "bell")
    }
    .badge(unreadCount)
```

### 7.6 Search

Place search using `.searchable()`. Provide search suggestions and support recent searches.

```swift
NavigationStack {
    List(searchResults) { item in
        ItemRow(item: item)
    }
    .searchable(text: $query, prompt: "Search products")
    .searchSuggestions {
        ForEach(recentSearches, id: \.self) { term in
            Text(term)
                .searchCompletion(term)
        }
    }
}
```

### 7.7 Context Menus

Use context menus (long press) for secondary actions. Never use a context menu as the only way to access an action.

```swift
ImageThumbnail(image: image)
    .contextMenu {
        Button { shareImage(image) } label: {
            Label("Share", systemImage: "square.and.arrow.up")
        }
        Button { copyImage(image) } label: {
            Label("Copy", systemImage: "doc.on.doc")
        }
        Divider()
        Button(role: .destructive) { deleteImage(image) } label: {
            Label("Delete", systemImage: "trash")
        }
    }
```

### 7.8 Forms and Input

**Text Fields:**
- 44pt minimum height
- Match keyboard type to input (`.emailAddress`, `.numberPad`, `.URL`)
- Clear button when text entered
- Placeholder uses `.quaternary` label color

```swift
Form {
    Section("Account") {
        TextField("Email", text: $email)
            .textContentType(.emailAddress)
            .keyboardType(.emailAddress)
            .autocapitalization(.none)
        
        SecureField("Password", text: $password)
            .textContentType(.password)
    }
    
    Section {
        Button("Sign In") { signIn() }
            .disabled(email.isEmpty || password.isEmpty)
    }
}
```

**Pickers:**
- Inline → 3-7 options
- Menu → 2-5 options (iOS 14+)
- Wheel → Date/time or long lists

### 7.9 Progress Indicators

- Determinate `ProgressView(value:total:)` for operations with known duration
- Indeterminate `ProgressView()` for unknown duration
- Never block the entire screen with a spinner

```swift
VStack {
    ProgressView(value: uploadProgress, total: 1.0)
        .progressViewStyle(.linear)
    
    Text("\(Int(uploadProgress * 100))% uploaded")
        .font(.caption)
        .foregroundStyle(.secondary)
}
```

---

## 8. Patterns

**Impact:** MEDIUM

### 8.1 Onboarding — Max 3 Pages, Skippable

Keep onboarding to 3 or fewer pages. Always provide a skip option. Defer sign-in until the user needs authenticated features.

```swift
TabView(selection: $currentPage) {
    OnboardingPage(icon: "sparkles", title: "Smart Features", description: "...")
        .tag(0)
    OnboardingPage(icon: "bell.badge", title: "Stay Notified", description: "...")
        .tag(1)
    OnboardingPage(icon: "lock.shield", title: "Private & Secure", description: "...")
        .tag(2)
}
.tabViewStyle(.page)
.overlay(alignment: .topTrailing) {
    Button("Skip") { finishOnboarding() }
        .padding()
}
```

### 8.2 Loading — Skeleton Views, No Blocking Spinners

Use skeleton/placeholder views that match the layout of the content being loaded. Never show a full-screen blocking spinner.

```swift
if isLoading {
    ForEach(0..<5, id: \.self) { _ in
        ArticleRowPlaceholder()
            .redacted(reason: .placeholder)
    }
} else {
    ForEach(articles) { article in
        ArticleRow(article: article)
    }
}
```

### 8.3 Launch Screen — Match First Screen

The launch storyboard must visually match the initial screen of the app. No splash logos, no branding screens. This creates the perception of instant launch.

### 8.4 Modality — Use Sparingly

Present modal views only when the user must complete or abandon a focused task. Always provide a clear dismiss action. Never stack modals on top of modals.

### 8.5 Notifications — High Value Only

Only send notifications for content the user genuinely cares about. Support actionable notifications. Categorize notifications so users can control them granularly.

### 8.6 Settings Placement

- Frequent settings: In-app settings screen accessible from a profile or gear icon
- Privacy/permission settings: Defer to the system Settings app via URL scheme
- Never duplicate system-level controls in-app

### 8.7 Action Sheets

For destructive or multiple-choice actions:

```swift
.confirmationDialog("Delete Photo?", isPresented: $showDelete, titleVisibility: .visible) {
    Button("Delete", role: .destructive) { deletePhoto() }
    Button("Cancel", role: .cancel) { }
} message: {
    Text("This action cannot be undone.")
}
```

- Destructive action at top (red)
- Cancel at bottom
- Dismiss by tapping outside

### 8.8 Pull-to-Refresh

Standard pattern for content updates:

```swift
List(items) { item in
    ItemRow(item: item)
}
.refreshable {
    await loadNewItems()
}
```

### 8.9 Haptic Feedback

Provide tactile response for significant actions:

| Generator | Usage |
|-----------|-------|
| `UIImpactFeedbackGenerator` | Physical impacts (.light, .medium, .heavy) |
| `UINotificationFeedbackGenerator` | Success, warning, error |
| `UISelectionFeedbackGenerator` | Selection changes |

```swift
Button("Complete") {
    let feedback = UINotificationFeedbackGenerator()
    feedback.notificationOccurred(.success)
    markComplete()
}
```

---

## 9. Privacy & Permissions

**Impact:** HIGH

### 9.1 Request Permissions in Context

Request a permission at the moment the user takes an action that needs it—never at app launch.

```swift
Button("Take Photo") {
    AVCaptureDevice.requestAccess(for: .video) { granted in
        if granted {
            showCamera = true
        }
    }
}
```

### 9.2 Explain Before System Prompt

Show a custom explanation screen before triggering the system permission dialog. The system dialog only appears once—if the user denies, the app must direct them to Settings.

```swift
struct LocationPermissionView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "location.fill")
                .font(.system(size: 48))
                .foregroundStyle(.blue)
            
            Text("Find Nearby Places")
                .font(.title2.bold())
            
            Text("We use your location to show relevant results. Your location is never stored or shared.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            
            Button("Enable Location") {
                locationManager.requestWhenInUseAuthorization()
            }
            .buttonStyle(.borderedProminent)
            
            Button("Not Now") { dismiss() }
                .foregroundStyle(.secondary)
        }
        .padding()
    }
}
```

### 9.3 Support Sign in with Apple

If the app offers any third-party sign-in (Google, Facebook), it must also offer Sign in with Apple. Present it as the first option.

### 9.4 Don't Require Accounts Unless Necessary

Let users explore the app before requiring sign-in. Gate only features that genuinely need authentication (purchases, sync, social features).

### 9.5 App Tracking Transparency

If you track users across apps or websites, display the ATT prompt. Respect denial—do not degrade the experience for users who opt out.

### 9.6 Location Button for One-Time Access

Use `LocationButton` for actions that need location once without requesting ongoing permission.

```swift
LocationButton(.currentLocation) {
    fetchNearbyResults()
}
.symbolVariant(.fill)
.labelStyle(.titleAndIcon)
```

---

## 10. System Integration

**Impact:** MEDIUM

### 10.1 Widgets for Glanceable Data

Provide widgets using WidgetKit for information users check frequently. Widgets are not interactive (beyond tapping to open the app), so show the most useful snapshot.

### 10.2 App Shortcuts for Key Actions

Define App Shortcuts so users can trigger key actions from Siri, Spotlight, and the Shortcuts app.

```swift
struct MyAppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: QuickAddIntent(),
            phrases: ["Add item in \(.applicationName)"],
            shortTitle: "Quick Add",
            systemImageName: "plus.circle"
        )
    }
}
```

### 10.3 Spotlight Indexing

Index app content with `CSSearchableItem` so users can find it from Spotlight search.

### 10.4 Share Sheet Integration

Support the system share sheet for content that users might want to send elsewhere.

```swift
ShareLink(item: article.url, subject: Text(article.title)) {
    Label("Share Article", systemImage: "square.and.arrow.up")
}
```

### 10.5 Live Activities

Use Live Activities and the Dynamic Island for real-time, time-bound events (delivery tracking, sports scores, workouts).

### 10.6 Handle Interruptions Gracefully

Save state and pause gracefully when interrupted by phone calls, Siri invocations, notifications, app switcher, or FaceTime SharePlay.

```swift
@Environment(\.scenePhase) private var scenePhase

var body: some View {
    ContentView()
        .onChange(of: scenePhase) { _, newPhase in
            switch newPhase {
            case .active:
                resumeActivity()
            case .inactive:
                pauseActivity()
            case .background:
                saveState()
            @unknown default:
                break
            }
        }
}
```

---

## Quick Reference

### Navigation & Structure

| Component | When to Use |
|-----------|-------------|
| `TabView` | 3-5 main app sections |
| `NavigationStack` | Hierarchical content drill-down |
| `.sheet` | Focused tasks requiring user completion |
| `.alert` | Decisions that block workflow |
| `.contextMenu` | Additional actions (always provide alternatives) |

### Data Display

| Component | When to Use |
|-----------|-------------|
| `List` | Scrollable rows with sections |
| `LazyVGrid` / `LazyHGrid` | Grid layouts |
| `.searchable` | Filterable content |
| `ProgressView` | Loading or task progress |

### User Input

| Component | When to Use |
|-----------|-------------|
| `TextField` | Single-line text |
| `TextEditor` | Multi-line text |
| `Picker` | Selection from options |
| `Toggle` | Binary on/off choice |
| `Stepper` | Numeric increment/decrement |

### System Features

| Component | When to Use |
|-----------|-------------|
| `ShareLink` | Content sharing |
| `LocationButton` | One-time location access |
| `PhotosPicker` | Image selection |
| `UIImpactFeedbackGenerator` | Tactile response |

---

## Anti-Patterns

Avoid these common HIG violations:

| Pattern | Problem | Solution |
|---------|---------|----------|
| Hamburger/drawer menu | Hides navigation, users miss features | Use TabView with 3-5 tabs |
| Broken back swipe | Custom gestures block system navigation | Keep NavigationStack default behavior |
| Full-screen spinner | App feels frozen, no progress indication | Use skeleton views with `.redacted()` |
| Logo splash screen | Artificial delay, wastes user time | Match launch screen to first view |
| Permissions at launch | Users deny without context | Request when action requires it |
| Fixed font sizes | Breaks Dynamic Type, accessibility issues | Use `.font(.body)` semantic styles |
| Color-only status | Colorblind users miss information | Add icons or text labels |
| Alert overuse | Interrupts flow for minor info | Use inline messages or banners |
| Hidden tab bar | Users lose navigation context | Keep tab bar visible on push |
| Content in unsafe areas | Text hidden under notch/Dynamic Island | Only ignore safe area for backgrounds |
| No modal dismiss | Users trapped in view | Add cancel button and swipe dismiss |
| Gesture-only actions | Accessibility users blocked | Provide button/menu alternatives |
| Small tap targets | Frequent mis-taps | Minimum 44x44pt hit area |
| Nested modals | Navigation confusion | Use NavigationStack within single sheet |
| Hardcoded colors | Broken in Dark Mode | Use semantic colors or asset variants |

---

## Review Checklist

Code review checklist for SwiftUI apps:

### Layout
- [ ] Interactive elements have 44pt minimum touch area
- [ ] Essential content stays within safe area bounds
- [ ] Main actions positioned for one-handed use (bottom)
- [ ] UI works across iPhone SE to Pro Max screen sizes
- [ ] Spacing uses 8pt increments

### Navigation
- [ ] Main sections use bottom TabView (3-5 tabs)
- [ ] No drawer/hamburger navigation
- [ ] Root views show large navigation titles
- [ ] System back gesture not blocked
- [ ] Tab state persists when switching

### Text & Fonts
- [ ] Text uses semantic styles (`.body`, `.headline`, etc.)
- [ ] Dynamic Type works at all sizes including accessibility
- [ ] Content reflows without truncation at large sizes
- [ ] No text below 11pt

### Colors
- [ ] Uses `.primary`, `.secondary`, `Color(.systemBackground)`
- [ ] Custom colors have light/dark variants in assets
- [ ] Status indicators combine color with icon/text
- [ ] Text contrast ratio meets WCAG AA

### Accessibility
- [ ] Icon buttons have `.accessibilityLabel()`
- [ ] VoiceOver order matches logical flow
- [ ] Animations respect `accessibilityReduceMotion`
- [ ] All actions have non-gesture alternatives

### Modals & Alerts
- [ ] Alerts reserved for critical decisions only
- [ ] Sheets provide clear dismiss mechanism
- [ ] No stacked modal presentations

### Permissions
- [ ] Permissions requested at point of use
- [ ] Pre-permission explanation screens used
- [ ] Core features work without sign-in

---

## iPad Adaptation

iPad users expect different interaction patterns:

**Layout:** Use `NavigationSplitView` for master-detail:

```swift
NavigationSplitView(columnVisibility: $columnVisibility) {
    SidebarView()
} content: {
    ListContentView()
} detail: {
    DetailView()
}
.navigationSplitViewStyle(.balanced)
```

**Presentation:** Action sheets become popovers automatically, but you can force popover:

```swift
.popover(isPresented: $showOptions) {
    OptionsView()
}
```

**Keyboard:** Add shortcuts for power users:

```swift
.keyboardShortcut("n", modifiers: .command)  // Cmd+N
```

**Drag & Drop:** Enable cross-app data transfer:

```swift
.draggable(item)
.dropDestination(for: Item.self) { items, location in
    handleDrop(items)
    return true
}
```

---

## Pre-Release Verification

Run through these scenarios before shipping:

**Visual consistency:**
- Switch between Light/Dark mode—does everything remain readable?
- Crank Dynamic Type to maximum—does layout adapt or break?
- Enable Bold Text—do custom fonts respond?

**Interaction quality:**
- Can you complete every action using only VoiceOver?
- Do all buttons feel tappable on first try (no mis-taps)?
- Does back-swipe work everywhere in navigation?

**Edge cases:**
- What happens on iPhone SE's small screen?
- What happens on iPad with keyboard attached?
- What shows when network fails mid-operation?
- What happens if user denies permissions?

**Platform compliance:**
- Are you using SF Symbols instead of custom icon PNGs?
- Are all colors from semantic palette or asset catalog with variants?
- Do destructive actions require explicit confirmation?

---

*SwiftUI, SF Symbols, Dynamic Island, and Apple are trademarks of Apple Inc.*
