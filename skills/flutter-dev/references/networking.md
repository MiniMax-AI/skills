# Networking

Dio configuration, interceptors, error handling, and caching strategies for Flutter network requests.

## Dio Setup

```dart
import 'package:dio/dio.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio dio;

  ApiClient._internal() {
    dio = Dio(BaseOptions(
      baseUrl: 'https://api.example.com/v1',
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      sendTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    dio.interceptors.addAll([
      AuthInterceptor(),
      LoggingInterceptor(),
      RetryInterceptor(dio: dio),
    ]);
  }
}
```

## Interceptors

### Auth Interceptor

```dart
class AuthInterceptor extends Interceptor {
  final TokenStorage _tokenStorage;

  AuthInterceptor({TokenStorage? tokenStorage})
      : _tokenStorage = tokenStorage ?? TokenStorage();

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await _tokenStorage.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      try {
        final newToken = await _refreshToken();
        if (newToken != null) {
          err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
          final response = await Dio().fetch(err.requestOptions);
          return handler.resolve(response);
        }
      } catch (e) {
        await _tokenStorage.clearTokens();
      }
    }
    handler.next(err);
  }

  Future<String?> _refreshToken() async {
    final refreshToken = await _tokenStorage.getRefreshToken();
    if (refreshToken == null) return null;

    final response = await Dio().post(
      'https://api.example.com/v1/auth/refresh',
      data: {'refresh_token': refreshToken},
    );

    if (response.statusCode == 200) {
      final newToken = response.data['access_token'];
      await _tokenStorage.saveAccessToken(newToken);
      return newToken;
    }
    return null;
  }
}
```

### Logging Interceptor

```dart
class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    debugPrint('→ ${options.method} ${options.uri}');
    if (options.data != null) {
      debugPrint('   Body: ${options.data}');
    }
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    debugPrint('← ${response.statusCode} ${response.requestOptions.uri}');
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    debugPrint('✗ ${err.response?.statusCode} ${err.requestOptions.uri}');
    debugPrint('   Error: ${err.message}');
    handler.next(err);
  }
}
```

### Retry Interceptor

```dart
class RetryInterceptor extends Interceptor {
  final Dio dio;
  final int maxRetries;
  final Duration retryDelay;

  RetryInterceptor({
    required this.dio,
    this.maxRetries = 3,
    this.retryDelay = const Duration(seconds: 1),
  });

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final retryCount = err.requestOptions.extra['retryCount'] ?? 0;

    if (_shouldRetry(err) && retryCount < maxRetries) {
      await Future.delayed(retryDelay * (retryCount + 1));

      err.requestOptions.extra['retryCount'] = retryCount + 1;

      try {
        final response = await dio.fetch(err.requestOptions);
        return handler.resolve(response);
      } catch (e) {
        return handler.next(err);
      }
    }

    handler.next(err);
  }

  bool _shouldRetry(DioException err) {
    return err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        (err.response?.statusCode ?? 0) >= 500;
  }
}
```

## Error Handling

### Custom Exception

```dart
sealed class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final dynamic data;

  const ApiException({
    required this.message,
    this.statusCode,
    this.data,
  });
}

class NetworkException extends ApiException {
  const NetworkException({super.message = 'Network connection failed'});
}

class ServerException extends ApiException {
  const ServerException({
    required super.message,
    super.statusCode,
    super.data,
  });
}

class UnauthorizedException extends ApiException {
  const UnauthorizedException({super.message = 'Authentication required'});
}

class ValidationException extends ApiException {
  final Map<String, List<String>> errors;

  const ValidationException({
    required this.errors,
    super.message = 'Validation failed',
  });
}
```

### Error Handler

```dart
class ApiErrorHandler {
  static ApiException handle(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return const NetworkException(message: 'Connection timeout');

      case DioExceptionType.connectionError:
        return const NetworkException(message: 'No internet connection');

      case DioExceptionType.badResponse:
        return _handleResponse(error.response);

      case DioExceptionType.cancel:
        return const ApiException(message: 'Request cancelled');

      default:
        return ApiException(message: error.message ?? 'Unknown error');
    }
  }

  static ApiException _handleResponse(Response? response) {
    final statusCode = response?.statusCode ?? 0;
    final data = response?.data;

    switch (statusCode) {
      case 400:
        if (data is Map && data.containsKey('errors')) {
          return ValidationException(
            errors: Map<String, List<String>>.from(
              (data['errors'] as Map).map(
                (k, v) => MapEntry(k.toString(), List<String>.from(v)),
              ),
            ),
          );
        }
        return ServerException(
          message: data?['message'] ?? 'Bad request',
          statusCode: statusCode,
        );

      case 401:
        return const UnauthorizedException();

      case 403:
        return const ServerException(
          message: 'Access denied',
          statusCode: 403,
        );

      case 404:
        return const ServerException(
          message: 'Resource not found',
          statusCode: 404,
        );

      case 422:
        return ValidationException(
          errors: _parseValidationErrors(data),
        );

      case >= 500:
        return ServerException(
          message: 'Server error',
          statusCode: statusCode,
        );

      default:
        return ServerException(
          message: data?['message'] ?? 'Unknown error',
          statusCode: statusCode,
        );
    }
  }

  static Map<String, List<String>> _parseValidationErrors(dynamic data) {
    if (data is! Map) return {};
    final errors = data['errors'];
    if (errors is! Map) return {};
    return errors.map((k, v) => MapEntry(
      k.toString(),
      v is List ? v.map((e) => e.toString()).toList() : [v.toString()],
    ));
  }
}
```

## Repository Pattern

```dart
abstract class BaseRepository {
  final Dio dio;

  BaseRepository(this.dio);

  Future<T> safeCall<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on DioException catch (e) {
      throw ApiErrorHandler.handle(e);
    }
  }
}

class UserRepository extends BaseRepository {
  UserRepository(super.dio);

  Future<User> getUser(String id) => safeCall(() async {
    final response = await dio.get('/users/$id');
    return User.fromJson(response.data);
  });

  Future<List<User>> getUsers({int page = 1, int limit = 20}) => safeCall(() async {
    final response = await dio.get('/users', queryParameters: {
      'page': page,
      'limit': limit,
    });
    return (response.data['data'] as List)
        .map((e) => User.fromJson(e))
        .toList();
  });

  Future<User> updateUser(String id, Map<String, dynamic> data) => safeCall(() async {
    final response = await dio.patch('/users/$id', data: data);
    return User.fromJson(response.data);
  });
}
```

## Caching

### Memory Cache

```dart
class CacheInterceptor extends Interceptor {
  final Map<String, CacheEntry> _cache = {};
  final Duration maxAge;

  CacheInterceptor({this.maxAge = const Duration(minutes: 5)});

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (options.method != 'GET') {
      handler.next(options);
      return;
    }

    final key = _cacheKey(options);
    final cached = _cache[key];

    if (cached != null && !cached.isExpired) {
      return handler.resolve(Response(
        requestOptions: options,
        data: cached.data,
        statusCode: 200,
      ));
    }

    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    if (response.requestOptions.method == 'GET') {
      final key = _cacheKey(response.requestOptions);
      _cache[key] = CacheEntry(
        data: response.data,
        expiry: DateTime.now().add(maxAge),
      );
    }
    handler.next(response);
  }

  String _cacheKey(RequestOptions options) {
    return '${options.uri}';
  }

  void invalidate(String pattern) {
    _cache.removeWhere((key, _) => key.contains(pattern));
  }

  void clear() => _cache.clear();
}

class CacheEntry {
  final dynamic data;
  final DateTime expiry;

  CacheEntry({required this.data, required this.expiry});

  bool get isExpired => DateTime.now().isAfter(expiry);
}
```

### Disk Cache with Hive

```dart
import 'package:hive_flutter/hive_flutter.dart';

class DiskCacheInterceptor extends Interceptor {
  static const String _boxName = 'api_cache';
  final Duration maxAge;

  DiskCacheInterceptor({this.maxAge = const Duration(hours: 1)});

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    if (options.method != 'GET') {
      handler.next(options);
      return;
    }

    final box = await Hive.openBox(_boxName);
    final key = _cacheKey(options);
    final cached = box.get(key);

    if (cached != null) {
      final entry = CachedResponse.fromJson(cached);
      if (!entry.isExpired) {
        return handler.resolve(Response(
          requestOptions: options,
          data: entry.data,
          statusCode: 200,
        ));
      }
    }

    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) async {
    if (response.requestOptions.method == 'GET') {
      final box = await Hive.openBox(_boxName);
      final key = _cacheKey(response.requestOptions);
      await box.put(key, CachedResponse(
        data: response.data,
        expiry: DateTime.now().add(maxAge),
      ).toJson());
    }
    handler.next(response);
  }

  String _cacheKey(RequestOptions options) => options.uri.toString();
}

class CachedResponse {
  final dynamic data;
  final DateTime expiry;

  CachedResponse({required this.data, required this.expiry});

  bool get isExpired => DateTime.now().isAfter(expiry);

  factory CachedResponse.fromJson(Map<String, dynamic> json) {
    return CachedResponse(
      data: json['data'],
      expiry: DateTime.parse(json['expiry']),
    );
  }

  Map<String, dynamic> toJson() => {
    'data': data,
    'expiry': expiry.toIso8601String(),
  };
}
```

## Riverpod Integration

```dart
@riverpod
Dio dio(Ref ref) {
  return ApiClient().dio;
}

@riverpod
UserRepository userRepository(Ref ref) {
  return UserRepository(ref.watch(dioProvider));
}

@riverpod
Future<User> user(Ref ref, String id) async {
  final repository = ref.watch(userRepositoryProvider);
  return repository.getUser(id);
}

@riverpod
class Users extends _$Users {
  @override
  Future<List<User>> build() => _fetch();

  Future<List<User>> _fetch() async {
    final repository = ref.watch(userRepositoryProvider);
    return repository.getUsers();
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }
}
```

## Request Cancellation

```dart
class SearchRepository extends BaseRepository {
  CancelToken? _searchToken;

  SearchRepository(super.dio);

  Future<List<SearchResult>> search(String query) async {
    _searchToken?.cancel();
    _searchToken = CancelToken();

    return safeCall(() async {
      final response = await dio.get(
        '/search',
        queryParameters: {'q': query},
        cancelToken: _searchToken,
      );
      return (response.data as List)
          .map((e) => SearchResult.fromJson(e))
          .toList();
    });
  }
}
```

## Common Patterns

| Pattern | Usage |
|---------|-------|
| Singleton client | Single Dio instance across app |
| Interceptor chain | Auth → Retry → Cache → Logging |
| Repository layer | Abstract API from business logic |
| Error mapping | Convert DioException to app exceptions |
| Cancel tokens | Debounce/cancel previous requests |
| Cache invalidation | Clear cache on mutations |

## Networking Checklist

| Item | Implementation |
|------|----------------|
| Base configuration | Timeouts, headers, base URL |
| Auth handling | Token injection, refresh on 401 |
| Error handling | Typed exceptions, user messages |
| Retry logic | Exponential backoff for transient errors |
| Request logging | Debug interceptor |
| Caching | Memory/disk cache for GET requests |
| Cancellation | Cancel tokens for search/debounce |

---

*Dio is an open-source package by the Flutter China community.*
