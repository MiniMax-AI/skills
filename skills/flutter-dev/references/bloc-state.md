# Bloc State Management

Bloc state management guide covering events, states, Cubit, and widget integration for complex business logic.

## When to Use Bloc

Use **Bloc/Cubit** when you need:
- Explicit event → state transitions
- Complex business logic with multiple events
- Predictable, testable state flows
- Clear separation between UI and logic

| Use Case | Recommended |
|----------|-------------|
| Simple mutable state | Riverpod |
| Computed values | Riverpod |
| Event-driven workflows | Bloc |
| Forms, auth, wizards | Bloc |
| Feature modules with complex logic | Bloc |

## Core Concepts

| Concept | Description |
|---------|-------------|
| Event | User or system input that triggers state change |
| State | Immutable representation of UI state |
| Bloc | Maps events to new states |
| Cubit | Simplified Bloc without events |

## Cubit (Recommended for Simpler Logic)

```dart
import 'package:flutter_bloc/flutter_bloc.dart';

class CounterCubit extends Cubit<int> {
  CounterCubit() : super(0);

  void increment() => emit(state + 1);
  void decrement() => emit(state - 1);
  void reset() => emit(0);
}
```

## Full Bloc Setup

### Event Definition

```dart
sealed class CounterEvent {}

final class CounterIncremented extends CounterEvent {}
final class CounterDecremented extends CounterEvent {}
final class CounterReset extends CounterEvent {}
```

### State Definition

```dart
class CounterState {
  final int value;
  final bool isLoading;

  const CounterState({
    required this.value,
    this.isLoading = false,
  });

  CounterState copyWith({int? value, bool? isLoading}) {
    return CounterState(
      value: value ?? this.value,
      isLoading: isLoading ?? this.isLoading,
    );
  }
}
```

### Bloc Implementation

```dart
class CounterBloc extends Bloc<CounterEvent, CounterState> {
  CounterBloc() : super(const CounterState(value: 0)) {
    on<CounterIncremented>(_onIncremented);
    on<CounterDecremented>(_onDecremented);
    on<CounterReset>(_onReset);
  }

  void _onIncremented(CounterIncremented event, Emitter<CounterState> emit) {
    emit(state.copyWith(value: state.value + 1));
  }

  void _onDecremented(CounterDecremented event, Emitter<CounterState> emit) {
    emit(state.copyWith(value: state.value - 1));
  }

  void _onReset(CounterReset event, Emitter<CounterState> emit) {
    emit(const CounterState(value: 0));
  }
}
```

## Providing Bloc to Widget Tree

```dart
// Single bloc
BlocProvider(
  create: (_) => CounterBloc(),
  child: const CounterScreen(),
);

// Multiple blocs
MultiBlocProvider(
  providers: [
    BlocProvider(create: (_) => AuthBloc()),
    BlocProvider(create: (_) => ProfileBloc()),
    BlocProvider(create: (_) => SettingsBloc()),
  ],
  child: const AppRoot(),
);
```

## Using Bloc in Widgets

### BlocBuilder (UI Rebuilds)

```dart
class CounterScreen extends StatelessWidget {
  const CounterScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<CounterBloc, CounterState>(
      buildWhen: (prev, curr) => prev.value != curr.value,
      builder: (context, state) {
        return Text(
          state.value.toString(),
          style: Theme.of(context).textTheme.displayLarge,
        );
      },
    );
  }
}
```

### BlocListener (Side Effects)

```dart
BlocListener<AuthBloc, AuthState>(
  listenWhen: (prev, curr) => prev.status != curr.status,
  listener: (context, state) {
    if (state.status == AuthStatus.failure) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(state.errorMessage ?? 'Error')),
      );
    }
    if (state.status == AuthStatus.authenticated) {
      context.go('/home');
    }
  },
  child: const LoginForm(),
);
```

### BlocConsumer (Builder + Listener)

```dart
BlocConsumer<FormBloc, FormState>(
  listenWhen: (prev, curr) => prev.status != curr.status,
  listener: (context, state) {
    if (state.status == FormStatus.success) {
      context.pop();
    }
  },
  buildWhen: (prev, curr) => prev.isValid != curr.isValid,
  builder: (context, state) {
    return ElevatedButton(
      onPressed: state.isValid
          ? () => context.read<FormBloc>().add(FormSubmitted())
          : null,
      child: const Text('Submit'),
    );
  },
);
```

### BlocSelector (Granular Rebuilds)

```dart
BlocSelector<UserBloc, UserState, String>(
  selector: (state) => state.user.name,
  builder: (context, name) {
    return Text('Hello, $name');
  },
);
```

## Async Bloc Pattern

```dart
on<UserRequested>((event, emit) async {
  emit(state.copyWith(status: UserStatus.loading));

  try {
    final user = await repository.fetchUser(event.userId);
    emit(state.copyWith(status: UserStatus.success, user: user));
  } catch (e) {
    emit(state.copyWith(status: UserStatus.failure, error: e.toString()));
  }
});
```

## Bloc + GoRouter Auth Guard

```dart
redirect: (context, state) {
  final authState = context.read<AuthBloc>().state;
  final isAuthRoute = state.matchedLocation.startsWith('/auth');

  if (authState.status != AuthStatus.authenticated && !isAuthRoute) {
    return '/auth/login';
  }
  if (authState.status == AuthStatus.authenticated && isAuthRoute) {
    return '/';
  }
  return null;
}
```

## Testing Bloc

```dart
import 'package:bloc_test/bloc_test.dart';

blocTest<CounterBloc, CounterState>(
  'emits incremented value when CounterIncremented added',
  build: () => CounterBloc(),
  act: (bloc) => bloc.add(CounterIncremented()),
  expect: () => [const CounterState(value: 1)],
);

blocTest<CounterBloc, CounterState>(
  'emits multiple states',
  build: () => CounterBloc(),
  act: (bloc) {
    bloc.add(CounterIncremented());
    bloc.add(CounterIncremented());
    bloc.add(CounterDecremented());
  },
  expect: () => [
    const CounterState(value: 1),
    const CounterState(value: 2),
    const CounterState(value: 1),
  ],
);
```

## Best Practices

| Do | Don't |
|----|-------|
| Keep states immutable | Mutate state directly |
| Use small, focused blocs | Create "god blocs" with everything |
| One feature = one bloc | Share blocs across unrelated features |
| Use Cubit for simple cases | Overcomplicate with Bloc unnecessarily |
| Test all state transitions | Skip bloc testing |
| Use `buildWhen`/`listenWhen` | Rebuild on every state change |

## Widget Reference

| Widget | Purpose |
|--------|---------|
| `BlocBuilder` | UI rebuilds based on state |
| `BlocListener` | Side effects (navigation, snackbar) |
| `BlocConsumer` | Both builder and listener |
| `BlocSelector` | Granular state selection |
| `BlocProvider` | Dependency injection |
| `MultiBlocProvider` | Multiple bloc injection |
| `RepositoryProvider` | Repository injection |

---

*Bloc is an open-source state management library by Felix Angelov.*
