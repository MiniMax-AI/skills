# Forms Reference

React Hook Form + Zod validation for React Native / Expo.

## Setup

```bash
npx expo install react-hook-form zod @hookform/resolvers
```

## Basic Form

```tsx
import { useForm, Controller } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

const schema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(8, "Min 8 characters"),
});
type FormData = z.infer<typeof schema>;

export function LoginForm({ onSubmit }: { onSubmit: (data: FormData) => void }) {
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  return (
    <View>
      {/* Controller pattern — repeat for each field */}
      <Controller
        control={control}
        name="email"
        render={({ field: { onChange, onBlur, value } }) => (
          <TextInput value={value} onChangeText={onChange} onBlur={onBlur}
            placeholder="Email" keyboardType="email-address" autoCapitalize="none" />
        )}
      />
      {errors.email && <Text style={styles.error}>{errors.email.message}</Text>}

      {/* Same Controller pattern for password, with secureTextEntry */}

      <Pressable onPress={handleSubmit(onSubmit)} disabled={isSubmitting}>
        <Text>{isSubmitting ? "Submitting..." : "Login"}</Text>
      </Pressable>
    </View>
  );
}
```

## Zod Schema Patterns

```tsx
import { z } from "zod";

// Registration form
const registerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(50),
  email: z.string().email("Invalid email address"),
  password: z.string()
    .min(8, "At least 8 characters")
    .regex(/[A-Z]/, "Must contain uppercase letter")
    .regex(/[0-9]/, "Must contain a number"),
  confirmPassword: z.string(),
  age: z.number({ invalid_type_error: "Age must be a number" }).int().min(18, "Must be 18+").optional(),
  role: z.enum(["admin", "user", "guest"]),
  agreedToTerms: z.literal(true, { errorMap: () => ({ message: "Must agree to terms" }) }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

// All-optional schema — use .optional() or .partial()
const profileSchema = registerSchema.pick({ name: true, email: true }).partial();

// Nested objects — compose schemas with z.array() and references
const addressSchema = z.object({ street: z.string().min(1), city: z.string().min(1), country: z.string().length(2) });
const orderSchema = z.object({ items: z.array(z.object({ productId: z.string(), quantity: z.number().int().positive() })).min(1), shippingAddress: addressSchema });
```

## Form State

```tsx
const {
  control,
  handleSubmit,
  watch,
  setValue,
  getValues,
  reset,
  setError,
  clearErrors,
  formState: {
    errors,
    isSubmitting,
    isValid,
    isDirty,           // Any field changed from defaultValues
    dirtyFields,       // Which fields changed
    touchedFields,     // Which fields were focused
  },
} = useForm<FormData>({ resolver: zodResolver(schema) });

// Watch a field value
const password = watch("password");
const allValues = watch(); // Watch all

// Set a value programmatically
setValue("email", "prefilled@example.com", { shouldValidate: true });

// Reset form
reset();                          // Back to defaultValues
reset({ email: "new@email.com" }); // Reset with new values

// Set server-side errors
setError("email", { message: "Email already in use" });
```

## Async Submit with Error Handling

```tsx
const { handleSubmit, setError } = useForm<FormData>();

const onSubmit = async (data: FormData) => {
  try {
    await api.post("/auth/register", data);
    router.replace("/home");
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      setError("email", { message: "Email already registered" });
    } else {
      setError("root", { message: "Something went wrong. Please try again." });
    }
  }
};

// Display root error
{errors.root && <Text style={styles.rootError}>{errors.root.message}</Text>}
```

## Multi-Step Forms

```tsx
const schema = z.object({
  step1: z.object({ name: z.string().min(1), email: z.string().email() }),
  step2: z.object({ phone: z.string(), address: z.string() }),
  step3: z.object({ password: z.string().min(8), confirmPassword: z.string() }),
});

type FormData = z.infer<typeof schema>;

export function MultiStepForm() {
  const [step, setStep] = useState(1);
  const { control, handleSubmit, trigger, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const nextStep = async () => {
    const stepKey = `step${step}` as keyof FormData;
    const valid = await trigger(stepKey); // Validate only current step's fields
    if (valid) setStep(s => s + 1);
  };

  // Render step component by index, with Back/Next/Submit navigation
  // Key pattern: trigger(stepKey) validates only current step before advancing
  return (/* StepOne | StepTwo | StepThree + Back/Next/Submit buttons */);

}
```

## Reusable Field Components

```tsx
// components/ui/FormField.tsx
import { Controller, Control, FieldValues, Path } from "react-hook-form";

interface FormFieldProps<T extends FieldValues> {
  control: Control<T>;
  name: Path<T>;
  label: string;
  placeholder?: string;
  secureTextEntry?: boolean;
  keyboardType?: TextInputProps["keyboardType"];
}

export function FormField<T extends FieldValues>({
  control, name, label, placeholder, secureTextEntry, keyboardType,
}: FormFieldProps<T>) {
  // Wraps Controller with: label, styled TextInput, and error message display
  // Uses fieldState.error for per-field error, accessibilityLabel for a11y
  return (
    <Controller control={control} name={name}
      render={({ field: { onChange, onBlur, value }, fieldState: { error } }) => (
        <View>
          <Text>{label}</Text>
          <TextInput value={value} onChangeText={onChange} onBlur={onBlur}
            placeholder={placeholder} secureTextEntry={secureTextEntry} keyboardType={keyboardType}
            style={[styles.input, error && styles.inputError]} accessibilityLabel={label} />
          {error && <Text style={styles.errorText}>{error.message}</Text>}
        </View>
      )}
    />
  );
}

// Usage
<FormField control={control} name="email" label="Email" keyboardType="email-address" />
<FormField control={control} name="password" label="Password" secureTextEntry />
```

## Dynamic Arrays

```tsx
import { useFieldArray } from "react-hook-form";

const schema = z.object({
  tags: z.array(z.object({ value: z.string().min(1) })).min(1, "Add at least one tag"),
});

function TagsForm() {
  const { control, handleSubmit } = useForm<z.infer<typeof schema>>();
  const { fields, append, remove } = useFieldArray({ control, name: "tags" });

  return (
    <View>
      {fields.map((field, index) => (
        <View key={field.id} style={{ flexDirection: "row" }}>
          <Controller
            control={control}
            name={`tags.${index}.value`}
            render={({ field: { onChange, value } }) => (
              <TextInput value={value} onChangeText={onChange} placeholder="Tag" />
            )}
          />
          <Pressable onPress={() => remove(index)}><Text>✕</Text></Pressable>
        </View>
      ))}
      <Pressable onPress={() => append({ value: "" })}><Text>+ Add Tag</Text></Pressable>
    </View>
  );
}
```

## Keyboard Handling

```tsx
import { KeyboardAvoidingView, Platform, ScrollView } from "react-native";

export function FormScreen() {
  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={{ flex: 1 }}
    >
      <ScrollView
        contentInsetAdjustmentBehavior="automatic"
        keyboardShouldPersistTaps="handled"  // Tapping outside keyboard doesn't dismiss
      >
        <LoginForm />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
```

## Testing Forms

```tsx
import { render, fireEvent, waitFor, screen } from "@testing-library/react-native";
import { userEvent } from "@testing-library/react-native";

it("validates required fields", async () => {
  render(<LoginForm onSubmit={jest.fn()} />);
  fireEvent.press(screen.getByText("Login")); // Submit without filling

  await waitFor(() => {
    expect(screen.getByText("Invalid email")).toBeTruthy();
    expect(screen.getByText("Min 8 characters")).toBeTruthy();
  });
});

it("submits with valid data", async () => {
  const onSubmit = jest.fn();
  const user = userEvent.setup();
  render(<LoginForm onSubmit={onSubmit} />);

  await user.type(screen.getByPlaceholderText("Email"), "user@example.com");
  await user.type(screen.getByPlaceholderText("Password"), "password123");
  await user.press(screen.getByText("Login"));

  await waitFor(() => {
    expect(onSubmit).toHaveBeenCalledWith({ email: "user@example.com", password: "password123" });
  });
});
```
