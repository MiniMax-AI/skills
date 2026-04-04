# Riverpod State Management

Riverpod 2.0 state management guide covering provider types, notifier patterns, and widget integration.

## Provider Types

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

// Simple computed value
final greetingProvider = Provider<String>((ref) {
  final name = ref.watch(userNameProvider);
  return 'Hello, $name';
});

// Simple mutable state
final counterProvider = StateProvider<int>((ref) => 0);

// Async state (API calls)
final usersProvider = FutureProvider<List<User>>((ref) async {
  final api = ref.read(apiProvider);
  return api.getUsers();
});

// Stream state (real-time)
final messagesProvider = StreamProvider<List<Message>>((ref) {
  return ref.read(chatServiceProvider).messagesStream;
});
```

### Provider Type Reference

| Provider | Use Case |
|----------|----------|
| `Provider` | Computed/derived values, dependency injection |
| `StateProvider` | Simple mutable state (counter, toggle) |
| `FutureProvider` | Async operations (one-time fetch) |
| `StreamProvider` | Real-time data streams |
| `NotifierProvider` | Complex state with methods |
| `AsyncNotifierProvider` | Async state with methods |

## Notifier Pattern (Riverpod 2.0)

### Synchronous Notifier

```dart
@riverpod
class TodoList extends _$TodoList {
  @override
  List<Todo> build() => [];

  void add(Todo todo) {
    state = [...state, todo];
  }

  void toggle(String id) {
    state = [
      for (final todo in state)
        if (todo.id == id) 
          todo.copyWith(completed: !todo.completed) 
        else 
          todo,
    ];
  }

  void remove(String id) {
    state = state.where((t) => t.id != id).toList();
  }
}
```

### Async Notifier

```dart
@riverpod
class UserProfile extends _$UserProfile {
  @override
  Future<User> build() async {
    return ref.read(apiProvider).getCurrentUser();
  }

  Future<void> updateName(String name) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final updated = await ref.read(apiProvider).updateUser(name: name);
      return updated;
    });
  }

  Future<void> refresh() async {
    ref.invalidateSelf();
    await future;
  }
}
```

## Usage in Widgets

### ConsumerWidget (Recommended)

```dart
class TodoScreen extends ConsumerWidget {
  const TodoScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final todos = ref.watch(todoListProvider);

    return ListView.builder(
      itemCount: todos.length,
      itemBuilder: (context, index) {
        final todo = todos[index];
        return ListTile(
          key: ValueKey(todo.id),
          title: Text(todo.title),
          leading: Checkbox(
            value: todo.completed,
            onChanged: (_) => ref.read(todoListProvider.notifier).toggle(todo.id),
          ),
        );
      },
    );
  }
}
```

### Selective Rebuilds with select

```dart
class UserAvatar extends ConsumerWidget {
  const UserAvatar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Only rebuilds when avatarUrl changes
    final avatarUrl = ref.watch(userProvider.select((u) => u?.avatarUrl));

    return CircleAvatar(
      backgroundImage: avatarUrl != null ? NetworkImage(avatarUrl) : null,
    );
  }
}
```

### Async State Handling

```dart
class UserProfileScreen extends ConsumerWidget {
  const UserProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userAsync = ref.watch(userProfileProvider);

    return userAsync.when(
      data: (user) => UserProfileContent(user: user),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, stack) => ErrorView(
        message: err.toString(),
        onRetry: () => ref.invalidate(userProfileProvider),
      ),
    );
  }
}
```

### Consumer for Scoped Rebuilds

```dart
class MyScreen extends StatelessWidget {
  const MyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const Text('Static content'),
        Consumer(
          builder: (context, ref, child) {
            final count = ref.watch(counterProvider);
            return Text('Count: $count');
          },
        ),
      ],
    );
  }
}
```

## Provider Modifiers

```dart
// Auto-dispose when no longer used
@riverpod
class AutoDisposeExample extends _$AutoDisposeExample {
  @override
  String build() => 'value';
}

// Family - parameterized providers
@riverpod
Future<User> userById(UserByIdRef ref, String id) async {
  return ref.read(apiProvider).getUser(id);
}

// Usage
final user = ref.watch(userByIdProvider('123'));
```

## Best Practices

| Do | Don't |
|----|-------|
| Use `ref.watch()` in build | Use `ref.watch()` in callbacks |
| Use `ref.read()` in callbacks | Use `ref.read()` in build |
| Use `select()` for granular rebuilds | Watch entire state unnecessarily |
| Create new state instances | Mutate state directly |
| Use `AsyncValue.guard()` for errors | Catch errors manually |

## Quick Reference

| Method | When to Use |
|--------|-------------|
| `ref.watch()` | In build method, rebuilds on change |
| `ref.read()` | In callbacks, one-time read |
| `ref.listen()` | Side effects on change |
| `ref.invalidate()` | Force provider refresh |
| `ref.refresh()` | Invalidate and get new value |

---

*Riverpod is an open-source state management library by Remi Rousselet.*
