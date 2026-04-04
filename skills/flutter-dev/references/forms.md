# Forms

Form validation, FormField patterns, input formatting, and reusable form components for Flutter.

## Basic Form Setup

```dart
class LoginForm extends StatefulWidget {
  const LoginForm({super.key});

  @override
  State<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends State<LoginForm> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      await authService.login(
        email: _emailController.text.trim(),
        password: _passwordController.text,
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _emailController,
            decoration: const InputDecoration(
              labelText: 'Email',
              prefixIcon: Icon(Icons.email_outlined),
            ),
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next,
            autocorrect: false,
            validator: Validators.email,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _passwordController,
            decoration: const InputDecoration(
              labelText: 'Password',
              prefixIcon: Icon(Icons.lock_outlined),
            ),
            obscureText: true,
            textInputAction: TextInputAction.done,
            onFieldSubmitted: (_) => _submit(),
            validator: Validators.password,
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _isLoading ? null : _submit,
            child: _isLoading
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Login'),
          ),
        ],
      ),
    );
  }
}
```

## Validators

```dart
class Validators {
  static String? required(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'This field is required';
    }
    return null;
  }

  static String? email(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Email is required';
    }
    final regex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
    if (!regex.hasMatch(value.trim())) {
      return 'Enter a valid email address';
    }
    return null;
  }

  static String? password(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    return null;
  }

  static String? strongPassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    if (!RegExp(r'[A-Z]').hasMatch(value)) {
      return 'Password must contain an uppercase letter';
    }
    if (!RegExp(r'[a-z]').hasMatch(value)) {
      return 'Password must contain a lowercase letter';
    }
    if (!RegExp(r'[0-9]').hasMatch(value)) {
      return 'Password must contain a number';
    }
    return null;
  }

  static String? phone(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Phone number is required';
    }
    final digits = value.replaceAll(RegExp(r'\D'), '');
    if (digits.length < 10 || digits.length > 15) {
      return 'Enter a valid phone number';
    }
    return null;
  }

  static String? minLength(int min) {
    return (String? value) {
      if (value == null || value.length < min) {
        return 'Must be at least $min characters';
      }
      return null;
    };
  }

  static String? maxLength(int max) {
    return (String? value) {
      if (value != null && value.length > max) {
        return 'Must be at most $max characters';
      }
      return null;
    };
  }

  static String? Function(String?) combine(List<String? Function(String?)> validators) {
    return (String? value) {
      for (final validator in validators) {
        final error = validator(value);
        if (error != null) return error;
      }
      return null;
    };
  }

  static String? match(String pattern, String message) {
    return (String? value) {
      if (value != null && !RegExp(pattern).hasMatch(value)) {
        return message;
      }
      return null;
    };
  }

  static String? confirmPassword(TextEditingController passwordController) {
    return (String? value) {
      if (value != passwordController.text) {
        return 'Passwords do not match';
      }
      return null;
    };
  }
}
```

## Input Formatters

```dart
import 'package:flutter/services.dart';

class PhoneInputFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    final digits = newValue.text.replaceAll(RegExp(r'\D'), '');
    final buffer = StringBuffer();

    for (int i = 0; i < digits.length && i < 10; i++) {
      if (i == 3 || i == 6) buffer.write('-');
      buffer.write(digits[i]);
    }

    return TextEditingValue(
      text: buffer.toString(),
      selection: TextSelection.collapsed(offset: buffer.length),
    );
  }
}

class CreditCardFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    final digits = newValue.text.replaceAll(RegExp(r'\D'), '');
    final buffer = StringBuffer();

    for (int i = 0; i < digits.length && i < 16; i++) {
      if (i > 0 && i % 4 == 0) buffer.write(' ');
      buffer.write(digits[i]);
    }

    return TextEditingValue(
      text: buffer.toString(),
      selection: TextSelection.collapsed(offset: buffer.length),
    );
  }
}

class CurrencyInputFormatter extends TextInputFormatter {
  final int decimalPlaces;

  CurrencyInputFormatter({this.decimalPlaces = 2});

  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    if (newValue.text.isEmpty) return newValue;

    final digits = newValue.text.replaceAll(RegExp(r'[^\d]'), '');
    if (digits.isEmpty) return const TextEditingValue(text: '');

    final value = int.parse(digits) / 100;
    final formatted = value.toStringAsFixed(decimalPlaces);

    return TextEditingValue(
      text: formatted,
      selection: TextSelection.collapsed(offset: formatted.length),
    );
  }
}

class UpperCaseFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    return newValue.copyWith(text: newValue.text.toUpperCase());
  }
}
```

### Using Formatters

```dart
TextFormField(
  decoration: const InputDecoration(labelText: 'Phone'),
  keyboardType: TextInputType.phone,
  inputFormatters: [
    FilteringTextInputFormatter.digitsOnly,
    PhoneInputFormatter(),
  ],
)

TextFormField(
  decoration: const InputDecoration(labelText: 'Amount'),
  keyboardType: const TextInputType.numberWithOptions(decimal: true),
  inputFormatters: [
    FilteringTextInputFormatter.allow(RegExp(r'[\d.]')),
    CurrencyInputFormatter(),
  ],
)
```

## Custom FormFields

### Dropdown FormField

```dart
class DropdownFormField<T> extends FormField<T> {
  DropdownFormField({
    super.key,
    required List<DropdownMenuItem<T>> items,
    super.initialValue,
    super.validator,
    super.onSaved,
    String? labelText,
    String? hintText,
    ValueChanged<T?>? onChanged,
  }) : super(
          builder: (state) {
            return InputDecorator(
              decoration: InputDecoration(
                labelText: labelText,
                errorText: state.errorText,
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<T>(
                  value: state.value,
                  hint: hintText != null ? Text(hintText) : null,
                  isExpanded: true,
                  items: items,
                  onChanged: (value) {
                    state.didChange(value);
                    onChanged?.call(value);
                  },
                ),
              ),
            );
          },
        );
}
```

### Checkbox FormField

```dart
class CheckboxFormField extends FormField<bool> {
  CheckboxFormField({
    super.key,
    required Widget label,
    super.initialValue = false,
    super.validator,
    super.onSaved,
  }) : super(
          builder: (state) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Checkbox(
                      value: state.value ?? false,
                      onChanged: state.didChange,
                    ),
                    Expanded(child: GestureDetector(
                      onTap: () => state.didChange(!(state.value ?? false)),
                      child: label,
                    )),
                  ],
                ),
                if (state.hasError)
                  Padding(
                    padding: const EdgeInsets.only(left: 12, top: 4),
                    child: Text(
                      state.errorText!,
                      style: TextStyle(
                        color: Theme.of(state.context).colorScheme.error,
                        fontSize: 12,
                      ),
                    ),
                  ),
              ],
            );
          },
        );
}
```

### Date Picker FormField

```dart
class DatePickerFormField extends FormField<DateTime> {
  DatePickerFormField({
    super.key,
    super.initialValue,
    super.validator,
    super.onSaved,
    String? labelText,
    DateTime? firstDate,
    DateTime? lastDate,
  }) : super(
          builder: (state) {
            return GestureDetector(
              onTap: () async {
                final picked = await showDatePicker(
                  context: state.context,
                  initialDate: state.value ?? DateTime.now(),
                  firstDate: firstDate ?? DateTime(1900),
                  lastDate: lastDate ?? DateTime(2100),
                );
                if (picked != null) {
                  state.didChange(picked);
                }
              },
              child: InputDecorator(
                decoration: InputDecoration(
                  labelText: labelText,
                  errorText: state.errorText,
                  suffixIcon: const Icon(Icons.calendar_today),
                ),
                child: Text(
                  state.value != null
                      ? DateFormat.yMMMd().format(state.value!)
                      : 'Select date',
                ),
              ),
            );
          },
        );
}
```

## Form with Hooks

```dart
import 'package:flutter_hooks/flutter_hooks.dart';

class HookLoginForm extends HookWidget {
  const HookLoginForm({super.key});

  @override
  Widget build(BuildContext context) {
    final formKey = useMemoized(GlobalKey<FormState>.new);
    final emailController = useTextEditingController();
    final passwordController = useTextEditingController();
    final emailFocus = useFocusNode();
    final passwordFocus = useFocusNode();
    final isLoading = useState(false);

    Future<void> submit() async {
      if (!formKey.currentState!.validate()) return;

      isLoading.value = true;
      try {
        await authService.login(
          email: emailController.text.trim(),
          password: passwordController.text,
        );
      } finally {
        isLoading.value = false;
      }
    }

    return Form(
      key: formKey,
      child: Column(
        children: [
          TextFormField(
            controller: emailController,
            focusNode: emailFocus,
            decoration: const InputDecoration(labelText: 'Email'),
            textInputAction: TextInputAction.next,
            onFieldSubmitted: (_) => passwordFocus.requestFocus(),
            validator: Validators.email,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: passwordController,
            focusNode: passwordFocus,
            decoration: const InputDecoration(labelText: 'Password'),
            obscureText: true,
            onFieldSubmitted: (_) => submit(),
            validator: Validators.password,
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: isLoading.value ? null : submit,
            child: isLoading.value
                ? const CircularProgressIndicator()
                : const Text('Login'),
          ),
        ],
      ),
    );
  }
}
```

## Server-Side Validation

```dart
class ServerValidationForm extends StatefulWidget {
  const ServerValidationForm({super.key});

  @override
  State<ServerValidationForm> createState() => _ServerValidationFormState();
}

class _ServerValidationFormState extends State<ServerValidationForm> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  Map<String, List<String>> _serverErrors = {};

  String? _emailValidator(String? value) {
    final clientError = Validators.email(value);
    if (clientError != null) return clientError;

    final serverError = _serverErrors['email'];
    if (serverError != null && serverError.isNotEmpty) {
      return serverError.first;
    }
    return null;
  }

  Future<void> _submit() async {
    setState(() => _serverErrors = {});

    if (!_formKey.currentState!.validate()) return;

    try {
      await api.register(email: _emailController.text);
    } on ValidationException catch (e) {
      setState(() => _serverErrors = e.errors);
      _formKey.currentState!.validate();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          TextFormField(
            controller: _emailController,
            decoration: const InputDecoration(labelText: 'Email'),
            validator: _emailValidator,
            onChanged: (_) {
              if (_serverErrors.containsKey('email')) {
                setState(() => _serverErrors.remove('email'));
              }
            },
          ),
          ElevatedButton(
            onPressed: _submit,
            child: const Text('Register'),
          ),
        ],
      ),
    );
  }
}
```

## Auto-Save Form

```dart
class AutoSaveForm extends StatefulWidget {
  const AutoSaveForm({super.key});

  @override
  State<AutoSaveForm> createState() => _AutoSaveFormState();
}

class _AutoSaveFormState extends State<AutoSaveForm> {
  final _formKey = GlobalKey<FormState>();
  Timer? _debounce;
  bool _hasChanges = false;

  void _onChanged() {
    setState(() => _hasChanges = true);

    _debounce?.cancel();
    _debounce = Timer(const Duration(seconds: 2), _autoSave);
  }

  Future<void> _autoSave() async {
    if (!_hasChanges) return;
    if (!_formKey.currentState!.validate()) return;

    _formKey.currentState!.save();
    await saveToServer();
    setState(() => _hasChanges = false);
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      onChanged: _onChanged,
      child: Column(
        children: [
          if (_hasChanges)
            const Text('Saving...', style: TextStyle(color: Colors.grey)),
          TextFormField(
            decoration: const InputDecoration(labelText: 'Title'),
            onSaved: (value) => saveField('title', value),
          ),
          TextFormField(
            decoration: const InputDecoration(labelText: 'Description'),
            maxLines: 3,
            onSaved: (value) => saveField('description', value),
          ),
        ],
      ),
    );
  }
}
```

## Common Keyboard Types

| Type | Usage |
|------|-------|
| `TextInputType.text` | General text |
| `TextInputType.emailAddress` | Email with @ keyboard |
| `TextInputType.phone` | Phone number pad |
| `TextInputType.number` | Numeric keyboard |
| `TextInputType.numberWithOptions(decimal: true)` | Numbers with decimal |
| `TextInputType.multiline` | Multi-line text |
| `TextInputType.url` | URL with shortcuts |

## Form Checklist

| Item | Implementation |
|------|----------------|
| GlobalKey | `GlobalKey<FormState>()` for form |
| Dispose controllers | Clean up in `dispose()` |
| Validation | Client + server-side |
| Input formatters | Phone, currency, etc. |
| Keyboard types | Match input type |
| Text actions | `textInputAction` for flow |
| Loading state | Disable during submission |
| Error display | Show below fields |

---

*Flutter and Material Design are trademarks of Google LLC.*
