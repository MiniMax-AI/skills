# Localization

Internationalization (i18n) patterns using flutter_localizations and intl package for Flutter applications.

## Setup

### Dependencies

```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_localizations:
    sdk: flutter
  intl: ^0.19.0

flutter:
  generate: true
```

### l10n Configuration

```yaml
# l10n.yaml
arb-dir: lib/l10n
template-arb-file: app_en.arb
output-localization-file: app_localizations.dart
output-class: AppLocalizations
nullable-getter: false
```

## ARB Files

### English (Template)

```json
// lib/l10n/app_en.arb
{
  "@@locale": "en",
  "appTitle": "My App",
  "@appTitle": {
    "description": "The application title"
  },
  "hello": "Hello",
  "welcome": "Welcome, {name}!",
  "@welcome": {
    "description": "Welcome message with user name",
    "placeholders": {
      "name": {
        "type": "String",
        "example": "John"
      }
    }
  },
  "itemCount": "{count, plural, =0{No items} =1{1 item} other{{count} items}}",
  "@itemCount": {
    "description": "Number of items",
    "placeholders": {
      "count": {
        "type": "int"
      }
    }
  },
  "lastUpdated": "Last updated: {date}",
  "@lastUpdated": {
    "description": "Last update timestamp",
    "placeholders": {
      "date": {
        "type": "DateTime",
        "format": "yMMMd"
      }
    }
  },
  "price": "Price: {amount}",
  "@price": {
    "description": "Product price",
    "placeholders": {
      "amount": {
        "type": "double",
        "format": "currency",
        "optionalParameters": {
          "symbol": "$",
          "decimalDigits": 2
        }
      }
    }
  },
  "gender": "{gender, select, male{He} female{She} other{They}} liked this",
  "@gender": {
    "description": "Gender-specific message",
    "placeholders": {
      "gender": {
        "type": "String"
      }
    }
  }
}
```

### Chinese

```json
// lib/l10n/app_zh.arb
{
  "@@locale": "zh",
  "appTitle": "我的应用",
  "hello": "你好",
  "welcome": "欢迎，{name}！",
  "itemCount": "{count, plural, =0{没有项目} other{{count} 个项目}}",
  "lastUpdated": "最后更新：{date}",
  "price": "价格：{amount}",
  "gender": "{gender, select, male{他} female{她} other{Ta}}喜欢了这个"
}
```

### Japanese

```json
// lib/l10n/app_ja.arb
{
  "@@locale": "ja",
  "appTitle": "マイアプリ",
  "hello": "こんにちは",
  "welcome": "ようこそ、{name}さん！",
  "itemCount": "{count, plural, =0{アイテムなし} other{{count}件}}",
  "lastUpdated": "最終更新：{date}",
  "price": "価格：{amount}",
  "gender": "{gender, select, male{彼} female{彼女} other{その人}}がいいねしました"
}
```

## App Configuration

```dart
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'My App',
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('en'),
        Locale('zh'),
        Locale('ja'),
      ],
      locale: const Locale('en'),
      home: const HomePage(),
    );
  }
}
```

## Using Translations

```dart
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.appTitle)),
      body: Column(
        children: [
          Text(l10n.hello),
          Text(l10n.welcome('John')),
          Text(l10n.itemCount(5)),
          Text(l10n.lastUpdated(DateTime.now())),
          Text(l10n.price(29.99)),
          Text(l10n.gender('female')),
        ],
      ),
    );
  }
}
```

### Extension for Convenience

```dart
extension LocalizationExtension on BuildContext {
  AppLocalizations get l10n => AppLocalizations.of(this);
}

// Usage
Text(context.l10n.hello)
```

## Dynamic Locale Switching

### With Riverpod

```dart
@riverpod
class LocaleNotifier extends _$LocaleNotifier {
  @override
  Locale build() {
    final saved = ref.watch(sharedPreferencesProvider).getString('locale');
    if (saved != null) {
      return Locale(saved);
    }
    return const Locale('en');
  }

  void setLocale(Locale locale) {
    ref.read(sharedPreferencesProvider).setString('locale', locale.languageCode);
    state = locale;
  }
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final locale = ref.watch(localeNotifierProvider);

    return MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      locale: locale,
      home: const HomePage(),
    );
  }
}
```

### Language Selector

```dart
class LanguageSelector extends ConsumerWidget {
  const LanguageSelector({super.key});

  static const languages = [
    (Locale('en'), 'English'),
    (Locale('zh'), '中文'),
    (Locale('ja'), '日本語'),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentLocale = ref.watch(localeNotifierProvider);

    return PopupMenuButton<Locale>(
      initialValue: currentLocale,
      onSelected: (locale) {
        ref.read(localeNotifierProvider.notifier).setLocale(locale);
      },
      itemBuilder: (context) => languages.map((lang) {
        return PopupMenuItem(
          value: lang.$1,
          child: Row(
            children: [
              if (currentLocale == lang.$1)
                const Icon(Icons.check, size: 18),
              const SizedBox(width: 8),
              Text(lang.$2),
            ],
          ),
        );
      }).toList(),
      child: const Icon(Icons.language),
    );
  }
}
```

## Date and Number Formatting

```dart
import 'package:intl/intl.dart';

class FormattingUtils {
  static String formatDate(DateTime date, String locale) {
    return DateFormat.yMMMd(locale).format(date);
  }

  static String formatDateTime(DateTime dateTime, String locale) {
    return DateFormat.yMMMd(locale).add_jm().format(dateTime);
  }

  static String formatRelativeTime(DateTime dateTime, String locale) {
    final now = DateTime.now();
    final diff = now.difference(dateTime);

    if (diff.inDays > 7) {
      return DateFormat.yMMMd(locale).format(dateTime);
    } else if (diff.inDays > 0) {
      return '${diff.inDays}d ago';
    } else if (diff.inHours > 0) {
      return '${diff.inHours}h ago';
    } else if (diff.inMinutes > 0) {
      return '${diff.inMinutes}m ago';
    } else {
      return 'Just now';
    }
  }

  static String formatCurrency(double amount, String locale, {String? symbol}) {
    return NumberFormat.currency(
      locale: locale,
      symbol: symbol,
      decimalDigits: 2,
    ).format(amount);
  }

  static String formatNumber(num number, String locale) {
    return NumberFormat.decimalPattern(locale).format(number);
  }

  static String formatPercent(double value, String locale) {
    return NumberFormat.percentPattern(locale).format(value);
  }

  static String formatCompact(num number, String locale) {
    return NumberFormat.compact(locale: locale).format(number);
  }
}
```

### Usage with Locale

```dart
class FormattedContent extends StatelessWidget {
  const FormattedContent({super.key});

  @override
  Widget build(BuildContext context) {
    final locale = Localizations.localeOf(context).toString();

    return Column(
      children: [
        Text(FormattingUtils.formatDate(DateTime.now(), locale)),
        Text(FormattingUtils.formatCurrency(1234.56, locale, symbol: '\$')),
        Text(FormattingUtils.formatNumber(1234567, locale)),
        Text(FormattingUtils.formatPercent(0.75, locale)),
        Text(FormattingUtils.formatCompact(1500000, locale)),
      ],
    );
  }
}
```

## RTL Support

```dart
class RtlAwareWidget extends StatelessWidget {
  const RtlAwareWidget({super.key});

  @override
  Widget build(BuildContext context) {
    final isRtl = Directionality.of(context) == TextDirection.rtl;

    return Row(
      children: [
        Icon(isRtl ? Icons.arrow_back : Icons.arrow_forward),
        const Expanded(child: Text('Content')),
        Padding(
          padding: EdgeInsetsDirectional.only(start: 16),
          child: const Icon(Icons.settings),
        ),
      ],
    );
  }
}
```

### Directional Widgets

| Standard | Directional |
|----------|-------------|
| `EdgeInsets` | `EdgeInsetsDirectional` |
| `Padding` | `Padding` with `EdgeInsetsDirectional` |
| `Align` | `AlignmentDirectional` |
| `Positioned` | `PositionedDirectional` |
| `BorderRadius` | `BorderRadiusDirectional` |

```dart
// Use directional
Padding(
  padding: const EdgeInsetsDirectional.only(start: 16, end: 8),
  child: child,
)

Container(
  alignment: AlignmentDirectional.centerStart,
  child: child,
)

Container(
  decoration: const BoxDecoration(
    borderRadius: BorderRadiusDirectional.only(
      topStart: Radius.circular(8),
      bottomStart: Radius.circular(8),
    ),
  ),
)
```

## Organized Translations

### Split by Feature

```
lib/
  l10n/
    app_en.arb          # Common translations
    app_zh.arb
    features/
      auth_en.arb       # Auth feature translations
      auth_zh.arb
      settings_en.arb   # Settings feature translations
      settings_zh.arb
```

### Namespaced Keys

```json
// app_en.arb
{
  "auth_login": "Login",
  "auth_logout": "Logout",
  "auth_forgotPassword": "Forgot Password?",

  "settings_title": "Settings",
  "settings_language": "Language",
  "settings_theme": "Theme",

  "error_network": "Network error. Please try again.",
  "error_unknown": "An unknown error occurred."
}
```

## Testing

```dart
void main() {
  testWidgets('shows localized text', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('en'),
        home: const HomePage(),
      ),
    );

    expect(find.text('Hello'), findsOneWidget);
  });

  testWidgets('switches locale', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          locale: const Locale('zh'),
          home: const HomePage(),
        ),
      ),
    );

    expect(find.text('你好'), findsOneWidget);
  });
}
```

## ARB Placeholders Reference

| Type | Format Options |
|------|----------------|
| `String` | None |
| `int` | `compact`, `compactCurrency`, `compactLong`, `compactSimpleCurrency` |
| `double` | `compact`, `compactCurrency`, `currency`, `decimalPattern`, `decimalPercentPattern`, `percentPattern`, `scientificPattern`, `simpleCurrency` |
| `DateTime` | Any `DateFormat` pattern (yMd, yMMMd, jm, etc.) |
| `num` | Same as `int` and `double` |

## Localization Checklist

| Item | Implementation |
|------|----------------|
| Dependencies | `flutter_localizations`, `intl` |
| l10n.yaml | Configure ARB paths and output |
| ARB files | Create for each supported locale |
| App config | Add delegates and supported locales |
| Generate | Run `flutter gen-l10n` |
| Use translations | `AppLocalizations.of(context)` |
| Date/number formatting | Use `intl` formatters with locale |
| RTL support | Use directional widgets |
| Persist preference | Save user's locale choice |
| Testing | Test with different locales |

---

*Flutter is a trademark of Google LLC. intl is an open-source package by the Dart team.*
