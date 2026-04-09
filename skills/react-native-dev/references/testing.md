# Testing Reference

Jest, React Native Testing Library, and E2E testing for Expo/React Native apps.

## Setup

```bash
npx expo install jest-expo @testing-library/react-native
```

```json
// package.json
{
  "jest": {
    "preset": "jest-expo",
    "setupFilesAfterSetup": ["@testing-library/react-native/extend-expect"]
  }
}
```

```bash
npx jest                    # Run all tests
npx jest --watch            # Watch mode
npx jest --coverage         # Coverage report
npx jest path/to/test.tsx   # Single file
```

## React Native Testing Library

### Basic Component Test

```tsx
// components/__tests__/Button.test.tsx
import { render, fireEvent, screen } from "@testing-library/react-native";
import { Button } from "../Button";

describe("Button", () => {
  it("renders label", () => {
    render(<Button label="Submit" onPress={() => {}} />);
    expect(screen.getByText("Submit")).toBeTruthy();
  });

  it("calls onPress when tapped", () => {
    const onPress = jest.fn();
    render(<Button label="Submit" onPress={onPress} />);
    fireEvent.press(screen.getByText("Submit"));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it("is disabled when loading", () => {
    render(<Button label="Submit" onPress={() => {}} loading />);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
```

### Queries

```tsx
// Prefer accessible queries
screen.getByRole("button", { name: "Submit" });
screen.getByLabelText("Email");
screen.getByPlaceholderText("Enter email");

// Text content
screen.getByText("Welcome back");
screen.getByText(/welcome/i);   // Regex — case insensitive

// Test IDs (last resort)
screen.getByTestId("user-avatar");

// Async queries
await screen.findByText("Loaded content");       // Waits for element to appear
await screen.findAllByRole("listitem");

// Non-existence
expect(screen.queryByText("Error")).toBeNull();
```

### User Events

```tsx
import { userEvent } from "@testing-library/react-native";

it("submits form on valid input", async () => {
  const user = userEvent.setup();
  render(<LoginForm onSubmit={mockSubmit} />);

  await user.type(screen.getByPlaceholderText("Email"), "user@example.com");
  await user.type(screen.getByPlaceholderText("Password"), "password123");
  await user.press(screen.getByRole("button", { name: "Login" }));

  expect(mockSubmit).toHaveBeenCalledWith({
    email: "user@example.com",
    password: "password123",
  });
});
```

### Testing Async State

```tsx
import { waitFor, act } from "@testing-library/react-native";

it("shows user data after loading", async () => {
  render(<UserProfile userId="123" />);

  // Loading state
  expect(screen.getByTestId("loading-indicator")).toBeTruthy();

  // Wait for data
  await waitFor(() => {
    expect(screen.getByText("John Doe")).toBeTruthy();
  });

  expect(screen.queryByTestId("loading-indicator")).toBeNull();
});
```

### Testing with React Query

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
}

function renderWithQuery(ui: ReactElement) {
  const client = createTestQueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

it("fetches and displays posts", async () => {
  // Mock fetch
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve([{ id: "1", title: "Post 1" }]),
  });

  renderWithQuery(<PostsList />);

  await waitFor(() => {
    expect(screen.getByText("Post 1")).toBeTruthy();
  });
});
```

### Testing with Zustand

```tsx
import { useAuthStore } from "../../stores/auth-store";

beforeEach(() => {
  // Reset store state before each test
  useAuthStore.setState({ user: null, token: null });
});

it("shows user name when logged in", () => {
  useAuthStore.setState({ user: { id: "1", name: "Alice" }, token: "tok" });
  render(<Header />);
  expect(screen.getByText("Alice")).toBeTruthy();
});
```

### Testing Navigation (Expo Router)

```tsx
import { renderRouter, screen } from "expo-router/testing-library";

it("navigates to detail screen", async () => {
  renderRouter({
    index: () => <HomeScreen />,
    "user/[id]": () => <UserScreen />,
  });

  fireEvent.press(screen.getByText("View Profile"));

  await waitFor(() => {
    expect(screen.getByTestId("user-screen")).toBeTruthy();
  });
});
```

## Mocking

### Mock Expo Modules

```tsx
// __mocks__/expo-secure-store.ts
export const getItemAsync = jest.fn().mockResolvedValue(null);
export const setItemAsync = jest.fn().mockResolvedValue(undefined);
export const deleteItemAsync = jest.fn().mockResolvedValue(undefined);
```

```tsx
// In test
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn().mockResolvedValue("mock-token"),
  setItemAsync: jest.fn(),
}));
```

### Mock fetch / API calls

```tsx
beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.restoreAllMocks();
});

it("handles API error", async () => {
  (global.fetch as jest.Mock).mockResolvedValue({
    ok: false,
    status: 500,
    json: () => Promise.resolve({ message: "Server error" }),
  });

  render(<UserProfile userId="123" />);

  await waitFor(() => {
    expect(screen.getByText("Server error")).toBeTruthy();
  });
});
```

### Mock react-native modules

```tsx
// jest.setup.ts
jest.mock("react-native/Libraries/Animated/NativeAnimatedHelper");

jest.mock("@react-native-community/netinfo", () => ({
  addEventListener: jest.fn(() => jest.fn()),
  fetch: jest.fn(() => Promise.resolve({ isConnected: true })),
}));
```

## Unit Tests (Non-UI Logic)

```tsx
// utils/__tests__/format.test.ts
import { formatCurrency, formatDate } from "../format";

describe("formatCurrency", () => {
  it("formats USD", () => expect(formatCurrency(1234.5, "USD")).toBe("$1,234.50"));
  it("handles zero", () => expect(formatCurrency(0, "USD")).toBe("$0.00"));
  it("handles negative", () => expect(formatCurrency(-50, "USD")).toBe("-$50.00"));
});
```

```tsx
// stores/__tests__/cart-store.test.ts
import { useCartStore } from "../cart-store";

beforeEach(() => useCartStore.setState({ items: [] }));

describe("CartStore", () => {
  it("adds item", () => {
    useCartStore.getState().add(mockProduct);
    expect(useCartStore.getState().items).toHaveLength(1);
  });

  it("calculates total", () => {
    useCartStore.getState().add({ ...mockProduct, price: 10 });
    expect(useCartStore.getState().total()).toBe(10);
  });
});
```

## E2E Testing (Maestro)

Maestro is the recommended E2E tool for Expo — no build configuration needed.

```bash
# Install
curl -Ls "https://get.maestro.mobile.dev" | bash

# Run flow
maestro test flows/login.yaml
```

```yaml
# flows/login.yaml
appId: com.example.myapp
---
- launchApp
- tapOn:
    text: "Sign In"
- inputText:
    id: "email-input"
    text: "user@example.com"
- inputText:
    id: "password-input"
    text: "password123"
- tapOn:
    text: "Login"
- assertVisible:
    text: "Welcome back"
- takeScreenshot: login-success
```

```yaml
# flows/create-post.yaml
appId: com.example.myapp
---
- launchApp
- runFlow: ./login.yaml
- tapOn:
    id: "new-post-button"
- inputText:
    id: "post-title"
    text: "My Test Post"
- tapOn:
    text: "Publish"
- assertVisible:
    text: "My Test Post"
```

## Testing Checklist

| Layer | What to Test |
|-------|-------------|
| Unit | Business logic, stores, utility functions, hooks |
| Component | Renders correctly, user interactions, loading/error states |
| Integration | Component + store/query working together |
| E2E | Critical user flows (login, checkout, core feature) |

## Common Mistakes

| Wrong | Right |
|-------|-------|
| `getByTestId` everywhere | Use accessible queries (`getByRole`, `getByLabelText`) |
| Testing implementation details | Test behavior the user sees |
| No `waitFor` on async operations | `waitFor` or `findBy*` for async |
| Real network calls in tests | Mock `fetch` or use MSW |
| Testing every line | Focus on behavior, not coverage %  |
