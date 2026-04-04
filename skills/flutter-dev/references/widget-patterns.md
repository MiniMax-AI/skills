# Widget Patterns

Flutter widget best practices covering const optimization, responsive layouts, hooks, and sliver patterns.

## Optimized Widget Pattern

Always use `const` constructors for static widgets to prevent unnecessary rebuilds:

```dart
class OptimizedCard extends StatelessWidget {
  final String title;
  final VoidCallback onTap;

  const OptimizedCard({
    super.key,
    required this.title,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(title, style: Theme.of(context).textTheme.titleMedium),
        ),
      ),
    );
  }
}
```

### Extracting Const Widgets

```dart
class MyScreen extends StatelessWidget {
  const MyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: const [
        _Header(),
        _Body(),
        _Footer(),
      ],
    );
  }
}

class _Header extends StatelessWidget {
  const _Header();

  @override
  Widget build(BuildContext context) {
    return const Text('Header');
  }
}
```

## Responsive Layout

```dart
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget? tablet;
  final Widget desktop;

  const ResponsiveLayout({
    super.key,
    required this.mobile,
    this.tablet,
    required this.desktop,
  });

  static const double mobileBreakpoint = 650;
  static const double desktopBreakpoint = 1100;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= desktopBreakpoint) return desktop;
        if (constraints.maxWidth >= mobileBreakpoint) return tablet ?? mobile;
        return mobile;
      },
    );
  }
}
```

### Breakpoint Reference

| Type | Width | Usage |
|------|-------|-------|
| Mobile | < 650pt | Single column, bottom nav |
| Tablet | 650-1100pt | Two columns, side nav optional |
| Desktop | > 1100pt | Multi-column, persistent nav |

## Custom Hooks (flutter_hooks)

```dart
import 'package:flutter_hooks/flutter_hooks.dart';

class CounterWidget extends HookWidget {
  const CounterWidget({super.key});

  @override
  Widget build(BuildContext context) {
    final counter = useState(0);
    final controller = useTextEditingController();
    final isMounted = useIsMounted();

    useEffect(() {
      debugPrint('Widget mounted');
      return () {
        debugPrint('Widget disposed');
      };
    }, const []);

    return Column(
      children: [
        Text('Count: ${counter.value}'),
        ElevatedButton(
          onPressed: () => counter.value++,
          child: const Text('Increment'),
        ),
        TextField(controller: controller),
      ],
    );
  }
}
```

### Common Hooks

| Hook | Purpose |
|------|---------|
| `useState` | Local state management |
| `useEffect` | Side effects with cleanup |
| `useMemoized` | Expensive computation caching |
| `useTextEditingController` | Text field controller |
| `useAnimationController` | Animation controller |
| `useFocusNode` | Focus management |
| `useIsMounted` | Check if widget is mounted |

## Sliver Patterns

```dart
CustomScrollView(
  slivers: [
    SliverAppBar(
      expandedHeight: 200,
      pinned: true,
      flexibleSpace: FlexibleSpaceBar(
        title: const Text('Title'),
        background: Image.network(imageUrl, fit: BoxFit.cover),
      ),
    ),
    SliverPadding(
      padding: const EdgeInsets.all(16),
      sliver: SliverList(
        delegate: SliverChildBuilderDelegate(
          (context, index) => ListTile(
            key: ValueKey(items[index].id),
            title: Text(items[index].title),
          ),
          childCount: items.length,
        ),
      ),
    ),
    const SliverToBoxAdapter(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Text('Footer'),
      ),
    ),
  ],
)
```

### Sliver Types

| Sliver | Usage |
|--------|-------|
| `SliverAppBar` | Collapsing app bar |
| `SliverList` | Lazy list |
| `SliverGrid` | Lazy grid |
| `SliverToBoxAdapter` | Single non-sliver widget |
| `SliverPadding` | Add padding to sliver |
| `SliverFillRemaining` | Fill remaining space |

## Key Usage Patterns

```dart
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    final item = items[index];
    return Dismissible(
      key: ValueKey(item.id),
      child: ListTile(
        key: ValueKey('tile_${item.id}'),
        title: Text(item.title),
      ),
    );
  },
)
```

| Key Type | When to Use |
|----------|-------------|
| `ValueKey` | Unique ID available |
| `ObjectKey` | Object identity matters |
| `UniqueKey` | Force rebuild |
| `GlobalKey` | Access state across tree |

## Optimization Checklist

| Pattern | Implementation |
|---------|----------------|
| const widgets | Add `const` to static widgets |
| Keys | Use `ValueKey` for list items |
| Select | `ref.watch(provider.select(...))` |
| RepaintBoundary | Isolate expensive repaints |
| ListView.builder | Lazy loading for lists |
| const constructors | Always use when possible |

---

*Flutter and Material Design are trademarks of Google LLC.*
