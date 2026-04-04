# Animations

Flutter animation patterns covering implicit animations, explicit animations, Hero transitions, and page transitions.

## Implicit Animations

Use implicit animations for simple property changes:

```dart
class ImplicitAnimationExample extends StatefulWidget {
  const ImplicitAnimationExample({super.key});

  @override
  State<ImplicitAnimationExample> createState() => _ImplicitAnimationExampleState();
}

class _ImplicitAnimationExampleState extends State<ImplicitAnimationExample> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => setState(() => _expanded = !_expanded),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
        width: _expanded ? 200 : 100,
        height: _expanded ? 200 : 100,
        decoration: BoxDecoration(
          color: _expanded ? Colors.blue : Colors.red,
          borderRadius: BorderRadius.circular(_expanded ? 16 : 8),
        ),
        child: const Center(child: Text('Tap me')),
      ),
    );
  }
}
```

### Common Implicit Widgets

| Widget | Animates |
|--------|----------|
| `AnimatedContainer` | Size, color, padding, decoration |
| `AnimatedOpacity` | Opacity |
| `AnimatedPadding` | Padding |
| `AnimatedPositioned` | Position in Stack |
| `AnimatedAlign` | Alignment |
| `AnimatedCrossFade` | Cross-fade between two widgets |
| `AnimatedSwitcher` | Transition between child widgets |
| `AnimatedDefaultTextStyle` | Text style |
| `AnimatedScale` | Scale transform |
| `AnimatedRotation` | Rotation transform |
| `AnimatedSlide` | Slide offset |

### AnimatedSwitcher

```dart
AnimatedSwitcher(
  duration: const Duration(milliseconds: 300),
  transitionBuilder: (child, animation) {
    return FadeTransition(
      opacity: animation,
      child: SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(0, 0.1),
          end: Offset.zero,
        ).animate(animation),
        child: child,
      ),
    );
  },
  child: _showFirst
      ? const Icon(Icons.check, key: ValueKey('check'))
      : const Icon(Icons.close, key: ValueKey('close')),
)
```

## Explicit Animations

Use explicit animations for complex, custom, or controlled animations:

```dart
class ExplicitAnimationExample extends StatefulWidget {
  const ExplicitAnimationExample({super.key});

  @override
  State<ExplicitAnimationExample> createState() => _ExplicitAnimationExampleState();
}

class _ExplicitAnimationExampleState extends State<ExplicitAnimationExample>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scaleAnimation;
  late final Animation<double> _rotationAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );

    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.2).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );

    _rotationAnimation = Tween<double>(begin: 0, end: 0.1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.elasticOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _controller.forward(),
      onTapUp: (_) => _controller.reverse(),
      onTapCancel: () => _controller.reverse(),
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Transform.scale(
            scale: _scaleAnimation.value,
            child: Transform.rotate(
              angle: _rotationAnimation.value,
              child: child,
            ),
          );
        },
        child: const Card(child: Padding(padding: EdgeInsets.all(24), child: Text('Press me'))),
      ),
    );
  }
}
```

### Animation with Hooks

```dart
import 'package:flutter_hooks/flutter_hooks.dart';

class AnimatedButtonHook extends HookWidget {
  const AnimatedButtonHook({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = useAnimationController(
      duration: const Duration(milliseconds: 300),
    );
    final scale = useAnimation(
      Tween<double>(begin: 1.0, end: 0.95).animate(
        CurvedAnimation(parent: controller, curve: Curves.easeInOut),
      ),
    );

    return GestureDetector(
      onTapDown: (_) => controller.forward(),
      onTapUp: (_) => controller.reverse(),
      onTapCancel: () => controller.reverse(),
      child: Transform.scale(
        scale: scale,
        child: const Card(child: Text('Animated Button')),
      ),
    );
  }
}
```

### Staggered Animations

```dart
class StaggeredAnimation extends StatefulWidget {
  const StaggeredAnimation({super.key});

  @override
  State<StaggeredAnimation> createState() => _StaggeredAnimationState();
}

class _StaggeredAnimationState extends State<StaggeredAnimation>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final List<Animation<double>> _itemAnimations;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );

    _itemAnimations = List.generate(5, (index) {
      final start = index * 0.1;
      final end = start + 0.4;
      return Tween<double>(begin: 0, end: 1).animate(
        CurvedAnimation(
          parent: _controller,
          curve: Interval(start, end.clamp(0, 1), curve: Curves.easeOut),
        ),
      );
    });

    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: List.generate(5, (index) {
        return AnimatedBuilder(
          animation: _itemAnimations[index],
          builder: (context, child) {
            return Opacity(
              opacity: _itemAnimations[index].value,
              child: Transform.translate(
                offset: Offset(0, 20 * (1 - _itemAnimations[index].value)),
                child: child,
              ),
            );
          },
          child: ListTile(title: Text('Item $index')),
        );
      }),
    );
  }
}
```

## Hero Animations

```dart
class HeroSourcePage extends StatelessWidget {
  const HeroSourcePage({super.key});

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
      ),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return GestureDetector(
          onTap: () => context.push('/detail/${item.id}'),
          child: Hero(
            tag: 'hero-${item.id}',
            child: Image.network(item.imageUrl, fit: BoxFit.cover),
          ),
        );
      },
    );
  }
}

class HeroDetailPage extends StatelessWidget {
  final String itemId;

  const HeroDetailPage({super.key, required this.itemId});

  @override
  Widget build(BuildContext context) {
    final item = getItem(itemId);
    return Scaffold(
      body: Column(
        children: [
          Hero(
            tag: 'hero-${item.id}',
            child: Image.network(item.imageUrl, fit: BoxFit.cover),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(item.title, style: Theme.of(context).textTheme.headlineMedium),
          ),
        ],
      ),
    );
  }
}
```

### Hero with Custom Flight

```dart
Hero(
  tag: 'avatar-$userId',
  flightShuttleBuilder: (
    flightContext,
    animation,
    flightDirection,
    fromHeroContext,
    toHeroContext,
  ) {
    return AnimatedBuilder(
      animation: animation,
      builder: (context, child) {
        return Material(
          color: Colors.transparent,
          child: CircleAvatar(
            radius: lerpDouble(24, 48, animation.value),
            backgroundImage: NetworkImage(avatarUrl),
          ),
        );
      },
    );
  },
  child: CircleAvatar(radius: 24, backgroundImage: NetworkImage(avatarUrl)),
)
```

## Page Transitions

### GoRouter Custom Transitions

```dart
GoRoute(
  path: '/detail/:id',
  pageBuilder: (context, state) {
    return CustomTransitionPage(
      key: state.pageKey,
      child: DetailPage(id: state.pathParameters['id']!),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return FadeTransition(
          opacity: animation,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 0.05),
              end: Offset.zero,
            ).animate(CurvedAnimation(
              parent: animation,
              curve: Curves.easeOut,
            )),
            child: child,
          ),
        );
      },
    );
  },
)
```

### Common Transition Patterns

```dart
extension PageTransitions on CustomTransitionPage {
  static CustomTransitionPage<T> fade<T>({
    required LocalKey key,
    required Widget child,
  }) {
    return CustomTransitionPage<T>(
      key: key,
      child: child,
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return FadeTransition(opacity: animation, child: child);
      },
    );
  }

  static CustomTransitionPage<T> slideUp<T>({
    required LocalKey key,
    required Widget child,
  }) {
    return CustomTransitionPage<T>(
      key: key,
      child: child,
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0, 1),
            end: Offset.zero,
          ).animate(CurvedAnimation(
            parent: animation,
            curve: Curves.easeOutCubic,
          )),
          child: child,
        );
      },
    );
  }

  static CustomTransitionPage<T> scale<T>({
    required LocalKey key,
    required Widget child,
  }) {
    return CustomTransitionPage<T>(
      key: key,
      child: child,
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return ScaleTransition(
          scale: Tween<double>(begin: 0.9, end: 1).animate(
            CurvedAnimation(parent: animation, curve: Curves.easeOut),
          ),
          child: FadeTransition(opacity: animation, child: child),
        );
      },
    );
  }
}
```

### Shared Axis Transition

```dart
import 'package:animations/animations.dart';

GoRoute(
  path: '/settings',
  pageBuilder: (context, state) {
    return CustomTransitionPage(
      key: state.pageKey,
      child: const SettingsPage(),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return SharedAxisTransition(
          animation: animation,
          secondaryAnimation: secondaryAnimation,
          transitionType: SharedAxisTransitionType.horizontal,
          child: child,
        );
      },
    );
  },
)
```

## Common Curves

| Curve | Usage |
|-------|-------|
| `Curves.easeInOut` | General purpose (default) |
| `Curves.easeOut` | Deceleration (entering) |
| `Curves.easeIn` | Acceleration (exiting) |
| `Curves.elasticOut` | Bouncy effect |
| `Curves.bounceOut` | Bounce at end |
| `Curves.fastOutSlowIn` | Material standard |
| `Curves.easeOutCubic` | Smooth deceleration |

## Animation Performance

```dart
class PerformantAnimation extends StatelessWidget {
  const PerformantAnimation({super.key});

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: AnimatedBuilder(
        animation: animation,
        builder: (context, child) {
          return Transform.translate(
            offset: Offset(animation.value * 100, 0),
            child: child,
          );
        },
        child: const ExpensiveWidget(),
      ),
    );
  }
}
```

### Performance Tips

| Tip | Implementation |
|-----|----------------|
| Use `child` parameter | Pass static content to `child` in `AnimatedBuilder` |
| `RepaintBoundary` | Isolate animated widgets |
| Avoid `Opacity` widget | Use `FadeTransition` instead |
| Prefer transforms | `Transform` is cheaper than layout changes |
| Pre-compute values | Calculate in `initState`, not `build` |

## Animation Checklist

| Item | Implementation |
|------|----------------|
| Simple animations | Use implicit widgets |
| Complex sequences | Use `AnimationController` |
| Widget transitions | `AnimatedSwitcher` with key |
| Cross-page elements | `Hero` with unique tags |
| Page transitions | `CustomTransitionPage` |
| Performance | `RepaintBoundary` + `child` parameter |

---

*Flutter and Material Design are trademarks of Google LLC.*
