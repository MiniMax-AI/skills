# GoRouter Navigation

GoRouter navigation guide covering route setup, guards, deep linking, and shell routes.

## Basic Setup

```dart
import 'package:go_router/go_router.dart';

final goRouter = GoRouter(
  initialLocation: '/',
  debugLogDiagnostics: true,
  redirect: (context, state) {
    final isLoggedIn = /* check auth state */;
    final isAuthRoute = state.matchedLocation.startsWith('/auth');
    
    if (!isLoggedIn && !isAuthRoute) {
      return '/auth/login';
    }
    if (isLoggedIn && isAuthRoute) {
      return '/';
    }
    return null;
  },
  routes: [
    GoRoute(
      path: '/',
      name: 'home',
      builder: (context, state) => const HomeScreen(),
      routes: [
        GoRoute(
          path: 'details/:id',
          name: 'details',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            final extra = state.extra as Map<String, dynamic>?;
            return DetailsScreen(id: id, title: extra?['title']);
          },
        ),
      ],
    ),
    GoRoute(
      path: '/auth/login',
      name: 'login',
      builder: (context, state) => const LoginScreen(),
    ),
  ],
);
```

### App Integration

```dart
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      routerConfig: goRouter,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
    );
  }
}
```

## Navigation Methods

```dart
// Navigate and replace entire stack
context.go('/details/123');

// Navigate and add to stack (can go back)
context.push('/details/123');

// Go back
context.pop();

// Go back with result
context.pop(result);

// Replace current route
context.pushReplacement('/home');

// Navigate with extra data
context.push('/details/123', extra: {'title': 'Item Title'});

// Navigate by name
context.goNamed('details', pathParameters: {'id': '123'});
context.pushNamed('details', pathParameters: {'id': '123'}, extra: data);
```

### Navigation Reference

| Method | Behavior |
|--------|----------|
| `context.go()` | Navigate, replace entire stack |
| `context.push()` | Navigate, add to stack |
| `context.pop()` | Go back one level |
| `context.pushReplacement()` | Replace current route |
| `context.goNamed()` | Navigate by route name |
| `context.canPop()` | Check if can go back |

## Shell Routes (Persistent UI)

```dart
final goRouter = GoRouter(
  routes: [
    ShellRoute(
      builder: (context, state, child) {
        return ScaffoldWithNavBar(child: child);
      },
      routes: [
        GoRoute(
          path: '/home',
          builder: (_, __) => const HomeScreen(),
        ),
        GoRoute(
          path: '/search',
          builder: (_, __) => const SearchScreen(),
        ),
        GoRoute(
          path: '/profile',
          builder: (_, __) => const ProfileScreen(),
        ),
      ],
    ),
  ],
);

class ScaffoldWithNavBar extends StatelessWidget {
  final Widget child;
  
  const ScaffoldWithNavBar({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _calculateSelectedIndex(context),
        onDestinationSelected: (index) => _onItemTapped(index, context),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
          NavigationDestination(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
  
  int _calculateSelectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    if (location.startsWith('/home')) return 0;
    if (location.startsWith('/search')) return 1;
    if (location.startsWith('/profile')) return 2;
    return 0;
  }
  
  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0: context.go('/home');
      case 1: context.go('/search');
      case 2: context.go('/profile');
    }
  }
}
```

## Query Parameters

```dart
GoRoute(
  path: '/search',
  builder: (context, state) {
    final query = state.uri.queryParameters['q'] ?? '';
    final page = int.tryParse(state.uri.queryParameters['page'] ?? '1') ?? 1;
    return SearchScreen(query: query, page: page);
  },
),

// Navigate with query params
context.go('/search?q=flutter&page=2');
context.goNamed('search', queryParameters: {'q': 'flutter', 'page': '2'});
```

## Riverpod Integration

```dart
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);
  
  return GoRouter(
    refreshListenable: authState,
    redirect: (context, state) {
      final isLoggedIn = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/auth');
      
      if (!isLoggedIn && !isAuthRoute) return '/auth/login';
      if (isLoggedIn && isAuthRoute) return '/';
      return null;
    },
    routes: [...],
  );
});

// In app.dart
class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(routerConfig: router);
  }
}
```

## Error Handling

```dart
final goRouter = GoRouter(
  errorBuilder: (context, state) {
    return ErrorScreen(error: state.error);
  },
  routes: [...],
);
```

## Deep Linking

Deep links work automatically when routes are configured with path parameters:

```dart
// URL: myapp://details/123
// or: https://myapp.com/details/123
GoRoute(
  path: '/details/:id',
  builder: (context, state) => DetailsScreen(id: state.pathParameters['id']!),
),
```

## Best Practices

| Do | Don't |
|----|-------|
| Use named routes for maintainability | Hardcode paths everywhere |
| Use `push()` for detail screens | Use `go()` for all navigation |
| Pass simple data via `extra` | Pass complex objects via URL |
| Use redirect for auth guards | Check auth in every screen |
| Use ShellRoute for persistent UI | Rebuild nav bar in every screen |

---

*GoRouter is an open-source navigation package for Flutter.*
