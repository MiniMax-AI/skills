# Performance Optimization

Flutter performance guide covering profiling, const optimization, and DevTools analysis.

## Profiling Commands

```bash
# Run in profile mode (required for accurate measurements)
flutter run --profile

# Analyze code issues
flutter analyze

# Launch DevTools
flutter pub global activate devtools
flutter pub global run devtools

# Build release for testing
flutter build apk --release
flutter build ios --release
```

## Const Widget Optimization

The most important optimization for preventing unnecessary rebuilds:

```dart
// BAD - Creates new objects every build
Widget build(BuildContext context) {
  return Container(
    padding: EdgeInsets.all(16),  // New object each time
    child: Text('Hello'),          // New widget each time
  );
}

// GOOD - Const prevents rebuilds
Widget build(BuildContext context) {
  return Container(
    padding: const EdgeInsets.all(16),
    child: const Text('Hello'),
  );
}
```

### Extracting Const Widgets

```dart
// BAD - Inline static content
class MyScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(Icons.star, size: 48),
        Text('Welcome'),
        Text('Description text here'),
      ],
    );
  }
}

// GOOD - Extract to const classes
class MyScreen extends StatelessWidget {
  const MyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        _Header(),
        _Description(),
      ],
    );
  }
}

class _Header extends StatelessWidget {
  const _Header();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        Icon(Icons.star, size: 48),
        Text('Welcome'),
      ],
    );
  }
}
```

## Selective Provider Watching

```dart
// BAD - Rebuilds on any user change
class UserAvatar extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(userProvider);
    return CircleAvatar(
      backgroundImage: NetworkImage(user.avatarUrl),
    );
  }
}

// GOOD - Only rebuilds when avatarUrl changes
class UserAvatar extends ConsumerWidget {
  const UserAvatar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final avatarUrl = ref.watch(userProvider.select((u) => u.avatarUrl));
    return CircleAvatar(
      backgroundImage: NetworkImage(avatarUrl),
    );
  }
}
```

## RepaintBoundary

Isolate expensive widgets to prevent unnecessary repaints:

```dart
// Isolate complex animated widgets
RepaintBoundary(
  child: ComplexAnimatedWidget(),
)

// Isolate frequently updating widgets
RepaintBoundary(
  child: StreamBuilder<int>(
    stream: counterStream,
    builder: (context, snapshot) => Text('${snapshot.data}'),
  ),
)
```

## List Optimization

```dart
// BAD - Builds all items upfront
ListView(
  children: items.map((item) => ItemWidget(item: item)).toList(),
)

// GOOD - Lazy loading with builder
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    return ItemWidget(
      key: ValueKey(items[index].id),
      item: items[index],
    );
  },
)

// For heterogeneous content
ListView.separated(
  itemCount: items.length,
  separatorBuilder: (_, __) => const Divider(),
  itemBuilder: (context, index) => ItemWidget(item: items[index]),
)
```

## Image Optimization

```dart
// Use cached_network_image for network images
CachedNetworkImage(
  imageUrl: url,
  placeholder: (_, __) => const ShimmerPlaceholder(),
  errorWidget: (_, __, ___) => const Icon(Icons.error),
  memCacheWidth: 200,
  memCacheHeight: 200,
)

// Resize images in memory
Image.network(
  url,
  cacheWidth: 200,   // Decode at smaller size
  cacheHeight: 200,  // Saves memory
)

// Precache images
precacheImage(NetworkImage(url), context);
```

## Heavy Computation

```dart
// BAD - Blocks UI thread
void processData() {
  final result = heavyComputation(data);  // UI freezes
  updateUI(result);
}

// GOOD - Run in isolate
Future<void> processData() async {
  final result = await compute(heavyComputation, data);
  updateUI(result);
}

// For multiple operations
Future<void> processMultiple() async {
  final results = await Future.wait([
    compute(process1, data1),
    compute(process2, data2),
    compute(process3, data3),
  ]);
}
```

## Animation Performance

```dart
// Use AnimatedBuilder for custom animations
AnimatedBuilder(
  animation: controller,
  builder: (context, child) {
    return Transform.rotate(
      angle: controller.value * 2 * pi,
      child: child,  // Child not rebuilt
    );
  },
  child: const ExpensiveWidget(),
)

// Prefer implicit animations for simple cases
AnimatedContainer(
  duration: const Duration(milliseconds: 300),
  width: expanded ? 200 : 100,
  child: const Content(),
)
```

## DevTools Analysis

### Key Metrics

| Metric | Target | Action if Exceeded |
|--------|--------|-------------------|
| Frame time | < 16ms (60fps) | Profile build/paint |
| Build time | < 8ms | Add const, extract widgets |
| Paint time | < 8ms | Add RepaintBoundary |
| Memory | Stable | Check for leaks |

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| Expensive builds | High build time | Extract const widgets |
| Excessive repaints | High paint time | Add RepaintBoundary |
| Memory leaks | Growing memory | Dispose controllers |
| Jank | Dropped frames | Use compute() |

## Performance Checklist

| Check | Solution |
|-------|----------|
| Unnecessary rebuilds | Add `const`, use `select()` |
| Large lists | Use `ListView.builder` |
| Image loading | Use `cached_network_image` |
| Heavy computation | Use `compute()` |
| Jank in animations | Use `RepaintBoundary` |
| Memory leaks | Dispose controllers, cancel subscriptions |
| Network calls | Cache responses, debounce requests |
| Startup time | Defer initialization, lazy loading |

## Dispose Pattern

```dart
class MyWidget extends StatefulWidget {
  const MyWidget({super.key});

  @override
  State<MyWidget> createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget> {
  late final TextEditingController _controller;
  late final StreamSubscription _subscription;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _subscription = stream.listen(handleData);
  }

  @override
  void dispose() {
    _controller.dispose();
    _subscription.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Container();
}
```

---

*Flutter and DevTools are trademarks of Google LLC.*

