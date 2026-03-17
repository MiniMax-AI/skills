# Swift Coding Standards

Best practices for writing clean, safe, and idiomatic Swift code following Apple's guidelines and modern Swift conventions.

---

## 1. Optionals and Safety

**Impact:** CRITICAL

Swift's optional system eliminates null pointer exceptions through compile-time safety.

### 1.1 Safe Unwrapping with if let

```swift
if let name = optionalName {
    print("Hello, \(name)")
}

// Multiple bindings
if let name = userName, let age = userAge, age >= 18 {
    print("\(name) is an adult")
}
```

### 1.2 Guard for Early Exit

Use `guard` to exit early when preconditions aren't met:

```swift
func processUser(_ user: User?) {
    guard let user = user else { return }
    guard !user.name.isEmpty else { return }
    print(user.name)
}
```

### 1.3 Nil Coalescing for Defaults

```swift
let displayName = name ?? "Anonymous"
let count = items?.count ?? 0
```

### 1.4 Optional Chaining

```swift
let count = user?.profile?.posts?.count
let uppercased = optionalString?.uppercased()
```

### 1.5 Optional map/flatMap

```swift
let uppercasedName = userName.map { $0.uppercased() }
let userID = userIDString.flatMap { Int($0) }
```

### 1.6 Never Force Unwrap

Avoid `!` force unwrapping. Use safe alternatives:

| Instead of | Use |
|------------|-----|
| `value!` | `if let value = value { }` |
| `array[0]` (unsafe) | `array.first` |
| `dictionary["key"]!` | `dictionary["key", default: defaultValue]` |

---

## 2. Naming Conventions

**Impact:** HIGH

### 2.1 Types: PascalCase

```swift
class UserProfileViewController { }
struct NetworkRequest { }
protocol DataSource { }
enum LoadingState { }
```

### 2.2 Variables and Functions: camelCase

```swift
var userName: String
let maximumRetryCount = 3
func fetchUserProfile() { }
```

### 2.3 Boolean Naming

Use `is`, `has`, `should`, `can` prefixes:

```swift
var isLoading: Bool
var hasCompletedOnboarding: Bool
var shouldShowAlert: Bool
var canEditProfile: Bool
```

### 2.4 Function Naming

Use verb phrases, read like natural English:

```swift
// Good - clear actions
func fetchUsers() async throws -> [User]
func remove(_ item: Item, at index: Int)
func makeIterator() -> Iterator

// Avoid - unclear or redundant
func getUsersData() // "get" is redundant
func doRemove() // vague
```

### 2.5 Parameter Labels

First parameter label can be omitted when obvious:

```swift
func insert(_ element: Element, at index: Int)
func move(from source: Int, to destination: Int)
```

---

## 3. Protocol-Oriented Design

**Impact:** HIGH

Swift favors composition over inheritance through protocols.

### 3.1 Define Capabilities Through Protocols

```swift
protocol DataStore {
    func save<T: Codable>(_ item: T, key: String) throws
    func load<T: Codable>(key: String) throws -> T?
}

protocol Drawable {
    var color: Color { get set }
    func draw()
}
```

### 3.2 Protocol Extensions for Default Behavior

```swift
extension Drawable {
    func draw() {
        print("Drawing with \(color)")
    }
}

extension Collection {
    func chunked(into size: Int) -> [[Element]] {
        stride(from: 0, to: count, by: size).map {
            Array(self[$0..<Swift.min($0 + size, count)])
        }
    }
}
```

### 3.3 Associated Types for Flexibility

```swift
protocol Repository {
    associatedtype Item
    func fetchAll() async throws -> [Item]
    func save(_ item: Item) async throws
}

class UserRepository: Repository {
    typealias Item = User
    
    func fetchAll() async throws -> [User] { /* ... */ }
    func save(_ item: User) async throws { /* ... */ }
}
```

### 3.4 Protocol Composition

```swift
protocol Named { var name: String { get } }
protocol Aged { var age: Int { get } }

func greet(_ person: Named & Aged) {
    print("Hello, \(person.name), age \(person.age)")
}
```

---

## 4. Value Types vs Reference Types

**Impact:** HIGH

### 4.1 Prefer Structs (Value Types)

Use structs for simple data models, independent copies:

```swift
struct User {
    var name: String
    var email: String
}

struct Point {
    var x: Double
    var y: Double
}
```

### 4.2 Use Classes When Needed

Use classes for shared mutable state, identity matters:

```swift
class NetworkManager {
    static let shared = NetworkManager()
    private init() { }
}

class FileHandle {
    // Wrapping system resource
}
```

### 4.3 Enums for Finite States

```swift
enum LoadingState {
    case idle
    case loading
    case success(Data)
    case failure(Error)
}

enum Result<Success, Failure: Error> {
    case success(Success)
    case failure(Failure)
}
```

| Type | Use When |
|------|----------|
| `struct` | Data models, coordinates, independent values |
| `class` | Shared state, identity matters, inheritance needed |
| `enum` | Finite set of options, state machines |

---

## 5. Memory Management with ARC

**Impact:** CRITICAL

### 5.1 Breaking Retain Cycles with weak

```swift
class Apartment {
    weak var tenant: Person?
}

class Person {
    var apartment: Apartment?
}
```

### 5.2 Closure Capture Lists

```swift
// Weak capture for optional self
onComplete = { [weak self] in
    self?.processResult()
}

// Capture specific values
let id = user.id
fetchData { [id] result in
    print("Fetched for \(id)")
}
```

### 5.3 unowned for Guaranteed Lifetime

Use when reference should never be nil during object lifetime:

```swift
class CreditCard {
    unowned let customer: Customer
    
    init(customer: Customer) {
        self.customer = customer
    }
}
```

| Keyword | Use When |
|---------|----------|
| `weak` | Reference may become nil |
| `unowned` | Reference guaranteed to outlive |
| None | Strong ownership needed |

---

## 6. Error Handling

**Impact:** HIGH

### 6.1 Define Typed Errors

```swift
enum NetworkError: Error {
    case invalidURL
    case noConnection
    case serverError(statusCode: Int)
    case decodingFailed(underlying: Error)
}

enum ValidationError: LocalizedError {
    case emptyField(name: String)
    case invalidFormat(field: String, expected: String)
    
    var errorDescription: String? {
        switch self {
        case .emptyField(let name):
            return "\(name) cannot be empty"
        case .invalidFormat(let field, let expected):
            return "\(field) must be \(expected)"
        }
    }
}
```

### 6.2 Throwing Functions

```swift
func fetchUser(id: Int) throws -> User {
    guard let url = URL(string: "https://api.example.com/users/\(id)") else {
        throw NetworkError.invalidURL
    }
    // ... implementation
}
```

### 6.3 Do-Catch Handling

```swift
do {
    let user = try fetchUser(id: 123)
    print(user.name)
} catch NetworkError.serverError(let code) {
    print("Server error: \(code)")
} catch NetworkError.noConnection {
    print("Check your internet connection")
} catch {
    print("Unknown error: \(error)")
}
```

### 6.4 try? and try!

```swift
// try? returns optional (nil on error)
let user = try? fetchUser(id: 123)

// try! crashes on error - use only when failure is programmer error
let config = try! loadBundledConfig()
```

### 6.5 Rethrows

```swift
func perform<T>(_ operation: () throws -> T) rethrows -> T {
    return try operation()
}
```

---

## 7. Modern Concurrency (async/await)

**Impact:** CRITICAL

### 7.1 Async Functions

```swift
func fetchUser(id: Int) async throws -> User {
    guard let url = URL(string: "https://api.example.com/users/\(id)") else {
        throw NetworkError.invalidURL
    }
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(User.self, from: data)
}

// Calling async functions
Task {
    do {
        let user = try await fetchUser(id: 123)
        print(user.name)
    } catch {
        print("Failed: \(error)")
    }
}
```

### 7.2 Parallel Execution with TaskGroup

```swift
func fetchAllUsers(ids: [Int]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        for id in ids {
            group.addTask {
                try await fetchUser(id: id)
            }
        }
        return try await group.reduce(into: []) { $0.append($1) }
    }
}
```

### 7.3 async let for Concurrent Bindings

```swift
async let user = fetchUser(id: 1)
async let posts = fetchPosts(userId: 1)
async let followers = fetchFollowers(userId: 1)

let profile = try await ProfileData(
    user: user,
    posts: posts,
    followers: followers
)
```

### 7.4 Actors for Thread-Safe State

```swift
actor BankAccount {
    private var balance: Double = 0
    
    func deposit(_ amount: Double) {
        balance += amount
    }
    
    func withdraw(_ amount: Double) throws {
        guard balance >= amount else {
            throw BankError.insufficientFunds
        }
        balance -= amount
    }
    
    func getBalance() -> Double {
        balance
    }
}

// Usage
let account = BankAccount()
await account.deposit(100)
let balance = await account.getBalance()
```

### 7.5 MainActor for UI Updates

```swift
@MainActor
class ViewModel: ObservableObject {
    @Published var isLoading = false
    @Published var users: [User] = []
    
    func loadUsers() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            users = try await fetchUsers()
        } catch {
            // Handle error
        }
    }
}
```

### 7.6 Task Cancellation

```swift
func fetchWithTimeout() async throws -> Data {
    try await withThrowingTaskGroup(of: Data.self) { group in
        group.addTask {
            try await fetchData()
        }
        group.addTask {
            try await Task.sleep(for: .seconds(10))
            throw TimeoutError()
        }
        
        let result = try await group.next()!
        group.cancelAll()
        return result
    }
}

// Check for cancellation
func longOperation() async throws {
    for item in items {
        try Task.checkCancellation()
        await process(item)
    }
}
```

---

## 8. Access Control

**Impact:** MEDIUM

### 8.1 Access Levels

| Level | Scope |
|-------|-------|
| `private` | Enclosing declaration only |
| `fileprivate` | Entire source file |
| `internal` | Module (default) |
| `public` | Other modules can access |
| `open` | Other modules can subclass/override |

### 8.2 Best Practices

```swift
public class UserService {
    // Public API
    public func fetchUser(id: Int) async throws -> User { }
    
    // Internal helper
    func buildRequest(for id: Int) -> URLRequest { }
    
    // Private implementation detail
    private let session: URLSession
    private var cache: [Int: User] = [:]
}
```

### 8.3 Private Setters

```swift
public struct Counter {
    public private(set) var count = 0
    
    public mutating func increment() {
        count += 1
    }
}
```

---

## 9. Generics and Type Constraints

**Impact:** MEDIUM

### 9.1 Generic Functions

```swift
func swapValues<T>(_ a: inout T, _ b: inout T) {
    let temp = a
    a = b
    b = temp
}
```

### 9.2 Type Constraints

```swift
func findIndex<T: Equatable>(of value: T, in array: [T]) -> Int? {
    array.firstIndex(of: value)
}

func decode<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
    try JSONDecoder().decode(type, from: data)
}
```

### 9.3 Where Clauses

```swift
func allMatch<C: Collection>(_ collection: C, predicate: (C.Element) -> Bool) -> Bool
    where C.Element: Equatable {
    collection.allSatisfy(predicate)
}

extension Array where Element: Numeric {
    func sum() -> Element {
        reduce(0, +)
    }
}
```

### 9.4 Opaque Types (some)

```swift
func makeCollection() -> some Collection {
    [1, 2, 3]
}

var body: some View {
    Text("Hello")
}
```

---

## 10. Property Wrappers

**Impact:** MEDIUM

### 10.1 Common SwiftUI Property Wrappers

| Wrapper | Use Case |
|---------|----------|
| `@State` | View-local mutable state |
| `@Binding` | Two-way connection to parent state |
| `@StateObject` | View-owned observable object |
| `@ObservedObject` | Passed-in observable object |
| `@EnvironmentObject` | Shared object from ancestor |
| `@Environment` | System environment values |
| `@Published` | Observable property in class |

### 10.2 Custom Property Wrappers

```swift
@propertyWrapper
struct Clamped<Value: Comparable> {
    private var value: Value
    let range: ClosedRange<Value>
    
    var wrappedValue: Value {
        get { value }
        set { value = min(max(newValue, range.lowerBound), range.upperBound) }
    }
    
    init(wrappedValue: Value, _ range: ClosedRange<Value>) {
        self.range = range
        self.value = min(max(wrappedValue, range.lowerBound), range.upperBound)
    }
}

struct Settings {
    @Clamped(0...100) var volume: Int = 50
}
```

---

## Quick Reference

### Optionals

```swift
if let x = optional { }      // Safe unwrap
guard let x = optional else { return }  // Early exit
let x = optional ?? default  // Default value
optional?.method()           // Optional chaining
optional.map { transform($0) }  // Transform if present
```

### Common Patterns

```swift
// Defer for cleanup
func process() {
    let file = openFile()
    defer { closeFile(file) }
    // ... work with file
}

// Lazy initialization
lazy var expensive: ExpensiveObject = {
    ExpensiveObject()
}()

// Type inference
let numbers = [1, 2, 3]  // [Int]
let doubled = numbers.map { $0 * 2 }  // [Int]
```

### Closure Syntax

```swift
// Full syntax
let sorted = names.sorted(by: { (s1: String, s2: String) -> Bool in
    return s1 < s2
})

// Shortened
let sorted = names.sorted { $0 < $1 }

// Trailing closure
UIView.animate(withDuration: 0.3) {
    view.alpha = 0
}
```

---

## Checklist

### Safety
- [ ] No force unwrapping (`!`) except for IB outlets and known-safe cases
- [ ] All optionals handled with `if let`, `guard let`, or `??`
- [ ] No implicitly unwrapped optionals (`!`) in data models

### Memory
- [ ] Closures use `[weak self]` when capturing self in escaping closures
- [ ] Delegate properties are `weak`
- [ ] No retain cycles between objects

### Concurrency
- [ ] Async functions used instead of completion handlers
- [ ] Actors protect shared mutable state
- [ ] UI updates on `@MainActor`
- [ ] Task cancellation checked in long operations

### Access Control
- [ ] `private` used for implementation details
- [ ] `public` API is minimal and intentional
- [ ] No unnecessary `internal` exposure

### Naming
- [ ] Types use PascalCase
- [ ] Functions and variables use camelCase
- [ ] Booleans have `is`/`has`/`should` prefix
- [ ] Functions read like natural English

---

*Swift and Apple are trademarks of Apple Inc.*
