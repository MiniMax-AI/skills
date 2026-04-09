# Testing Strategies

Flutter testing guide covering widget tests, unit tests, integration tests, and mocking patterns.

## Test Types

| Type | Purpose | Speed | Scope |
|------|---------|-------|-------|
| Unit tests | Business logic, utilities | Fast | Single function/class |
| Widget tests | UI components | Medium | Single widget |
| Integration tests | Full user flows | Slow | Multiple screens |

## Widget Tests

### Basic Widget Test

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Counter increments when button tapped', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: CounterScreen()));

    // Verify initial state
    expect(find.text('0'), findsOneWidget);
    expect(find.text('1'), findsNothing);

    // Tap the increment button
    await tester.tap(find.byIcon(Icons.add));
    await tester.pump();

    // Verify state changed
    expect(find.text('0'), findsNothing);
    expect(find.text('1'), findsOneWidget);
  });
}
```

### Testing with Riverpod

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('displays user name from provider', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          userProvider.overrideWithValue(
            AsyncValue.data(User(name: 'Test User')),
          ),
        ],
        child: const MaterialApp(home: UserScreen()),
      ),
    );

    expect(find.text('Test User'), findsOneWidget);
  });

  testWidgets('shows loading indicator', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          userProvider.overrideWithValue(const AsyncValue.loading()),
        ],
        child: const MaterialApp(home: UserScreen()),
      ),
    );

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('shows error message', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          userProvider.overrideWithValue(
            AsyncValue.error('Network error', StackTrace.current),
          ),
        ],
        child: const MaterialApp(home: UserScreen()),
      ),
    );

    expect(find.text('Network error'), findsOneWidget);
  });
}
```

### Testing with Bloc

```dart
import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class MockCounterBloc extends MockBloc<CounterEvent, CounterState>
    implements CounterBloc {}

void main() {
  late MockCounterBloc mockBloc;

  setUp(() {
    mockBloc = MockCounterBloc();
  });

  testWidgets('displays current count', (tester) async {
    when(() => mockBloc.state).thenReturn(const CounterState(value: 42));

    await tester.pumpWidget(
      MaterialApp(
        home: BlocProvider<CounterBloc>.value(
          value: mockBloc,
          child: const CounterScreen(),
        ),
      ),
    );

    expect(find.text('42'), findsOneWidget);
  });

  testWidgets('calls increment on button tap', (tester) async {
    when(() => mockBloc.state).thenReturn(const CounterState(value: 0));

    await tester.pumpWidget(
      MaterialApp(
        home: BlocProvider<CounterBloc>.value(
          value: mockBloc,
          child: const CounterScreen(),
        ),
      ),
    );

    await tester.tap(find.byIcon(Icons.add));

    verify(() => mockBloc.add(CounterIncremented())).called(1);
  });
}
```

## Bloc Tests

```dart
import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class MockUserRepository extends Mock implements UserRepository {}

void main() {
  late MockUserRepository mockRepository;

  setUp(() {
    mockRepository = MockUserRepository();
  });

  group('UserBloc', () {
    blocTest<UserBloc, UserState>(
      'emits loading then success when user loaded',
      setUp: () {
        when(() => mockRepository.getUser())
            .thenAnswer((_) async => User(name: 'Test'));
      },
      build: () => UserBloc(repository: mockRepository),
      act: (bloc) => bloc.add(UserRequested()),
      expect: () => [
        const UserState(status: UserStatus.loading),
        UserState(status: UserStatus.success, user: User(name: 'Test')),
      ],
    );

    blocTest<UserBloc, UserState>(
      'emits loading then failure when error occurs',
      setUp: () {
        when(() => mockRepository.getUser())
            .thenThrow(Exception('Network error'));
      },
      build: () => UserBloc(repository: mockRepository),
      act: (bloc) => bloc.add(UserRequested()),
      expect: () => [
        const UserState(status: UserStatus.loading),
        isA<UserState>()
            .having((s) => s.status, 'status', UserStatus.failure),
      ],
    );
  });
}
```

## Unit Tests

```dart
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Validator', () {
    test('returns error for empty email', () {
      expect(Validator.email(''), 'Email is required');
    });

    test('returns error for invalid email', () {
      expect(Validator.email('invalid'), 'Invalid email format');
    });

    test('returns null for valid email', () {
      expect(Validator.email('test@example.com'), isNull);
    });
  });

  group('Calculator', () {
    late Calculator calculator;

    setUp(() {
      calculator = Calculator();
    });

    test('adds two numbers', () {
      expect(calculator.add(2, 3), 5);
    });

    test('throws on division by zero', () {
      expect(() => calculator.divide(10, 0), throwsArgumentError);
    });
  });
}
```

## Mocking with Mocktail

```dart
import 'package:mocktail/mocktail.dart';

// Create mock classes
class MockApiService extends Mock implements ApiService {}
class MockStorageService extends Mock implements StorageService {}

// Register fallback values for complex types
setUpAll(() {
  registerFallbackValue(User(name: 'fallback'));
});

void main() {
  late MockApiService mockApi;

  setUp(() {
    mockApi = MockApiService();
  });

  test('fetches user from API', () async {
    // Arrange
    when(() => mockApi.getUser(any()))
        .thenAnswer((_) async => User(name: 'Test'));

    // Act
    final repository = UserRepository(api: mockApi);
    final user = await repository.getUser('123');

    // Assert
    expect(user.name, 'Test');
    verify(() => mockApi.getUser('123')).called(1);
  });
}
```

## Integration Tests

```dart
// integration_test/app_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:my_app/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('complete login flow', (tester) async {
    app.main();
    await tester.pumpAndSettle();

    // Navigate to login
    await tester.tap(find.text('Login'));
    await tester.pumpAndSettle();

    // Enter credentials
    await tester.enterText(
      find.byKey(const Key('email_field')),
      'test@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('password_field')),
      'password123',
    );

    // Submit form
    await tester.tap(find.text('Sign In'));
    await tester.pumpAndSettle();

    // Verify navigation to home
    expect(find.text('Welcome'), findsOneWidget);
  });
}
```

Run integration tests:

```bash
flutter test integration_test/app_test.dart
```

## Test Helpers

```dart
// test/helpers/pump_app.dart
extension PumpApp on WidgetTester {
  Future<void> pumpApp(Widget widget, {List<Override>? overrides}) {
    return pumpWidget(
      ProviderScope(
        overrides: overrides ?? [],
        child: MaterialApp(
          home: widget,
        ),
      ),
    );
  }
}

// Usage
await tester.pumpApp(const MyWidget());
```

## Golden Tests

```dart
testWidgets('matches golden', (tester) async {
  await tester.pumpWidget(const MaterialApp(home: MyWidget()));

  await expectLater(
    find.byType(MyWidget),
    matchesGoldenFile('goldens/my_widget.png'),
  );
});
```

Update goldens:

```bash
flutter test --update-goldens
```

## Testing Checklist

| Test Type | What to Test |
|-----------|--------------|
| Widget tests | UI rendering, user interactions, state changes |
| Bloc tests | Event → state transitions, async operations |
| Unit tests | Validators, formatters, utilities, models |
| Integration tests | Critical user flows, navigation |

---

*Flutter and flutter_test are trademarks of Google LLC.*
