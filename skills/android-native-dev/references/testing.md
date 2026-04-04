# Testing

Detailed examples and patterns for each Android test layer. Read the section relevant to the layer you're working with.

## Table of Contents

1. [Local Unit Tests (JUnit + Robolectric)](#1-local-unit-tests-junit--robolectric)
2. [Instrumentation Tests (Espresso)](#2-instrumentation-tests-espresso)
3. [UI Automator (Cross-App & System UI)](#3-ui-automator-cross-app--system-ui)
4. [Compose UI Testing](#4-compose-ui-testing)
5. [Gradle Managed Devices](#5-gradle-managed-devices)

---

## 1. Local Unit Tests (JUnit + Robolectric)

Local tests live in `src/test/` and run on the JVM — no emulator needed, so they're fast (milliseconds each). Use them for ViewModels, Repositories, mappers, validators, and any pure logic.

### Basic ViewModel Test

```kotlin
class CounterViewModelTest {
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()  // see below

    private lateinit var viewModel: CounterViewModel

    @Before
    fun setup() {
        viewModel = CounterViewModel()
    }

    @Test
    fun `increment updates count`() = runTest {
        viewModel.increment()
        assertEquals(1, viewModel.uiState.value.count)
    }
}
```

### Testing Coroutines (Critical)

The Main dispatcher doesn't exist on the JVM. Replace it with `TestDispatcher` or tests crash with `IllegalStateException`.

```kotlin
// Reusable rule — put in a shared test-util module
class MainDispatcherRule(
    private val dispatcher: TestDispatcher = UnconfinedTestDispatcher()
) : TestWatcher() {
    override fun starting(description: Description) {
        Dispatchers.setMain(dispatcher)
    }
    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```

```kotlin
// ❌ Wrong: No Main dispatcher replacement → crash
@Test
fun `load data`() = runTest {
    val vm = MyViewModel(repo)
    vm.load()  // launches on Dispatchers.Main → IllegalStateException
}

// ✅ Correct: Use MainDispatcherRule
@get:Rule
val mainDispatcherRule = MainDispatcherRule()

@Test
fun `load data`() = runTest {
    val vm = MyViewModel(repo)
    vm.load()
    assertEquals(UiState.Success, vm.uiState.value)
}
```

### Testing StateFlow with Turbine

```kotlin
@Test
fun `loading then success states`() = runTest {
    val vm = MyViewModel(fakeRepo)

    vm.uiState.test {   // Turbine extension
        assertEquals(UiState.Idle, awaitItem())
        vm.load()
        assertEquals(UiState.Loading, awaitItem())
        assertEquals(UiState.Success(data), awaitItem())
        cancelAndIgnoreRemainingEvents()
    }
}
```

### Mocking with MockK

```kotlin
@Test
fun `repository calls api and caches`() = runTest {
    val api = mockk<UserApi>()
    coEvery { api.getUser("42") } returns User("42", "Alice")

    val repo = UserRepository(api)
    val user = repo.getUser("42")

    assertEquals("Alice", user.name)
    coVerify(exactly = 1) { api.getUser("42") }
}
```

| MockK Function | Purpose                |
|----------------|------------------------|
| `mockk<T>()`  | Create mock instance   |
| `every { }`   | Stub synchronous calls |
| `coEvery { }` | Stub suspend functions |
| `verify { }`  | Verify call happened   |
| `coVerify { }` | Verify suspend call   |
| `slot<T>()`   | Capture argument value |

### Robolectric — When You Need Android Classes

Robolectric simulates the Android framework on the JVM, so tests stay fast while accessing `Context`, `SharedPreferences`, resources, etc.

```kotlin
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class PreferencesManagerTest {

    private lateinit var context: Context

    @Before
    fun setup() {
        context = ApplicationProvider.getApplicationContext()
    }

    @Test
    fun `saves and reads theme preference`() {
        val prefs = PreferencesManager(context)
        prefs.setDarkMode(true)
        assertTrue(prefs.isDarkMode())
    }
}
```

### Common Local Test Mistakes

```kotlin
// ❌ Wrong: Testing implementation details (fragile)
@Test
fun `check internal cache map size`() {
    repo.load()
    assertEquals(1, repo.cacheMap.size)  // breaks if cache strategy changes
}

// ✅ Correct: Test observable behavior
@Test
fun `second call returns cached result without network`() = runTest {
    coEvery { api.fetch() } returns data

    repo.load()
    repo.load()

    coVerify(exactly = 1) { api.fetch() }  // only one network call
}
```

---

## 2. Instrumentation Tests (Espresso)

Instrumentation tests live in `src/androidTest/` and run on a real device or emulator. Slower than local tests, but they exercise the actual Android stack — use them for UI flows, database integration, and cross-component interaction.

### Test Runner Setup

In `app/build.gradle.kts`:

```kotlin
android {
    defaultConfig {
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
}
```

### Espresso Basics

Espresso's API follows a consistent pattern: **find → act → assert**.

```kotlin
@RunWith(AndroidJUnit4::class)
class LoginScreenTest {

    @get:Rule
    val activityRule = ActivityScenarioRule(LoginActivity::class.java)

    @Test
    fun validLogin_navigatesToHome() {
        // Find and act
        onView(withId(R.id.email_input))
            .perform(typeText("user@example.com"), closeSoftKeyboard())
        onView(withId(R.id.password_input))
            .perform(typeText("secret123"), closeSoftKeyboard())
        onView(withId(R.id.login_button))
            .perform(click())

        // Assert
        onView(withId(R.id.home_container))
            .check(matches(isDisplayed()))
    }
}
```

| Category   | Common Matchers / Actions                                                          |
|------------|------------------------------------------------------------------------------------|
| **Find**   | `withId(R.id.x)`, `withText("x")`, `withContentDescription("x")`, `withHint("x")` |
| **Act**    | `click()`, `typeText("x")`, `clearText()`, `scrollTo()`, `swipeUp()`              |
| **Assert** | `isDisplayed()`, `withText("x")`, `isEnabled()`, `isChecked()`, `doesNotExist()`  |

### Testing Intents

Espresso-Intents lets you verify outgoing Intents and stub responses (e.g., camera, file picker).

```kotlin
@get:Rule
val intentsRule = IntentsRule()

@Test
fun shareButton_launchesShareIntent() {
    onView(withId(R.id.share_button)).perform(click())

    intended(allOf(
        hasAction(Intent.ACTION_SEND),
        hasType("text/plain")
    ))
}

@Test
fun cameraButton_handlesResult() {
    val resultData = Intent().apply { putExtra("photo_uri", "content://mock") }
    intending(hasAction(MediaStore.ACTION_IMAGE_CAPTURE))
        .respondWith(Instrumentation.ActivityResult(RESULT_OK, resultData))

    onView(withId(R.id.camera_button)).perform(click())
    onView(withId(R.id.photo_preview)).check(matches(isDisplayed()))
}
```

### IdlingResource for Async Operations

Espresso waits for the UI thread and AsyncTask by default, but not for custom async work (Retrofit, coroutines, etc.). `IdlingResource` tells Espresso when your app is busy.

```kotlin
// In production code (thin wrapper)
object NetworkIdlingResource {
    private val counter = CountingIdlingResource("Network")
    fun increment() = counter.increment()
    fun decrement() = counter.decrement()
    fun get(): IdlingResource = counter
}

// In test setup
@Before
fun registerIdling() {
    IdlingRegistry.getInstance().register(NetworkIdlingResource.get())
}

@After
fun unregisterIdling() {
    IdlingRegistry.getInstance().unregister(NetworkIdlingResource.get())
}
```

---

## 3. UI Automator (Cross-App & System UI)

UI Automator can interact with any visible UI — system dialogs, notifications, other apps. Use it when Espresso can't reach outside your app's process.

| Use Case                     | Why UI Automator                       |
|------------------------------|----------------------------------------|
| Runtime permission dialogs   | System UI, outside app process         |
| Notification actions         | System notification shade              |
| Device settings interaction  | Settings app                           |
| Multi-app workflows          | e.g., share to another app and return  |

```kotlin
@RunWith(AndroidJUnit4::class)
class PermissionFlowTest {

    private lateinit var device: UiDevice

    @Before
    fun setup() {
        device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
    }

    @Test
    fun grantsCameraPermission_andOpensCamera() {
        // Trigger permission request from within your app
        onView(withId(R.id.camera_button)).perform(click())

        // Handle the system permission dialog via UI Automator
        val allowButton = device.findObject(
            By.res("com.android.permissioncontroller:id/permission_allow_foreground_only_button")
        )
        allowButton?.click()

        // Back in Espresso territory — verify the camera view appeared
        onView(withId(R.id.camera_preview)).check(matches(isDisplayed()))
    }

    @Test
    fun notificationTap_opensDetail() {
        // Open notification shade
        device.openNotification()
        device.wait(Until.hasObject(By.textStartsWith("New message")), 5000)

        // Tap the notification
        val notification = device.findObject(By.textStartsWith("New message"))
        notification.click()

        // Verify deep-link target
        onView(withId(R.id.message_detail)).check(matches(isDisplayed()))
    }
}
```

---

## 4. Compose UI Testing

Compose has its own testing framework that works with the semantic tree rather than the view hierarchy. Tests can run as local tests (with Robolectric) or instrumentation tests — the API is the same.

### Basic Setup

```kotlin
@RunWith(AndroidJUnit4::class)
class GreetingScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun displaysGreeting_andRespondsToClick() {
        composeTestRule.setContent {
            MyAppTheme {
                GreetingScreen(name = "World")
            }
        }

        composeTestRule.onNodeWithText("Hello, World!")
            .assertIsDisplayed()

        composeTestRule.onNodeWithText("Say Hi")
            .performClick()

        composeTestRule.onNodeWithText("Hi back!")
            .assertIsDisplayed()
    }
}
```

### Finders, Assertions & Actions

| Category   | API                                          | Example                         |
|------------|----------------------------------------------|---------------------------------|
| **Find**   | `onNodeWithText("x")`                       | Matches visible text            |
|            | `onNodeWithTag("x")`                        | Matches `Modifier.testTag("x")` |
|            | `onNodeWithContentDescription("x")`         | Matches semantics label         |
|            | `onAllNodesWithTag("x")`                    | Returns list of matches         |
| **Assert** | `assertIsDisplayed()`                        | Node is visible                 |
|            | `assertTextEquals("x")`                     | Exact text match                |
|            | `assertIsEnabled()` / `assertIsNotEnabled()` | Enabled state                  |
|            | `assertDoesNotExist()`                       | Node not in tree               |
|            | `assertCountEquals(n)`                       | For `onAllNodes`               |
| **Act**    | `performClick()`                             | Tap                             |
|            | `performTextInput("x")`                     | Type into text field            |
|            | `performScrollTo()`                          | Scroll node into view          |
|            | `performTouchInput { swipeUp() }`           | Gestures                        |

### Using testTag for Reliable Selectors

Text-based finders break with localization or copy changes. Use `testTag` for stable selectors:

```kotlin
// ❌ Fragile: breaks if text changes or app is localized
composeTestRule.onNodeWithText("Submit Order").performClick()

// ✅ Stable: testTag doesn't change with locale
composeTestRule.onNodeWithTag("submit_order_button").performClick()
```

```kotlin
// In production Composable
Button(
    onClick = { /* ... */ },
    modifier = Modifier.testTag("submit_order_button")
) {
    Text(stringResource(R.string.submit_order))
}
```

### Testing with Activity Context

When your Composable needs a `ComponentActivity` (e.g., for `viewModel()` or navigation), use `createAndroidComposeRule`:

```kotlin
@get:Rule
val composeTestRule = createAndroidComposeRule<MainActivity>()

@Test
fun fullScreen_endToEnd() {
    // Activity is already launched — interact with the real content
    composeTestRule.onNodeWithTag("login_email")
        .performTextInput("user@test.com")
    composeTestRule.onNodeWithTag("login_password")
        .performTextInput("pass123")
    composeTestRule.onNodeWithTag("login_submit")
        .performClick()

    composeTestRule.waitUntil(timeoutMillis = 5000) {
        composeTestRule.onAllNodesWithTag("home_screen")
            .fetchSemanticsNodes().isNotEmpty()
    }

    composeTestRule.onNodeWithTag("home_screen")
        .assertIsDisplayed()
}
```

### Testing Navigation

```kotlin
@Test
fun navigatesToDetail_onItemClick() {
    val navController = TestNavHostController(ApplicationProvider.getApplicationContext())

    composeTestRule.setContent {
        navController.navigatorProvider.addNavigator(ComposeNavigator())
        MyAppNavHost(navController = navController)
    }

    // Click item on list screen
    composeTestRule.onNodeWithTag("item_0").performClick()

    // Verify navigation destination
    assertEquals("detail/0", navController.currentBackStackEntry?.destination?.route)
}
```

### Common Compose Test Mistakes

```kotlin
// ❌ Wrong: Asserting immediately after async operation
composeTestRule.onNodeWithTag("submit").performClick()
composeTestRule.onNodeWithText("Success").assertIsDisplayed()  // may fail — UI hasn't updated yet

// ✅ Correct: Wait for the UI to settle
composeTestRule.onNodeWithTag("submit").performClick()
composeTestRule.waitForIdle()
composeTestRule.onNodeWithText("Success").assertIsDisplayed()

// ✅ Also correct: waitUntil for longer async work
composeTestRule.onNodeWithTag("submit").performClick()
composeTestRule.waitUntil(timeoutMillis = 3000) {
    composeTestRule.onAllNodesWithText("Success")
        .fetchSemanticsNodes().isNotEmpty()
}
```

---

## 5. Gradle Managed Devices

Define emulator profiles in `build.gradle.kts` so anyone (including CI) can run instrumentation tests without manually creating AVDs. Gradle downloads the system image, creates the emulator, runs tests, and tears it down automatically.

### Device Configuration

In `app/build.gradle.kts`:

```kotlin
android {
    testOptions {
        managedDevices {
            localDevices {
                create("pixel6Api34") {
                    device = "Pixel 6"
                    apiLevel = 34
                    systemImageSource = "aosp-atd"  // ATD = faster, headless
                }
                create("pixel4Api30") {
                    device = "Pixel 4"
                    apiLevel = 30
                    systemImageSource = "aosp-atd"
                }
                create("smallTabletApi34") {
                    device = "Nexus 7"
                    apiLevel = 34
                    systemImageSource = "google"     // full Google APIs image
                }
            }

            // Group devices for matrix testing
            groups {
                create("phoneTests") {
                    targetDevices.add(devices["pixel6Api34"])
                    targetDevices.add(devices["pixel4Api30"])
                }
                create("allDevices") {
                    targetDevices.add(devices["pixel6Api34"])
                    targetDevices.add(devices["pixel4Api30"])
                    targetDevices.add(devices["smallTabletApi34"])
                }
            }
        }
    }
}
```

### System Image Sources

| Source         | Description                                       | Best For                     |
|----------------|---------------------------------------------------|------------------------------|
| `"aosp-atd"`   | Automated Test Device — minimal, no Play Services | Fast CI, pure logic tests    |
| `"google-atd"` | ATD with Google APIs                              | Tests needing Maps, Firebase |
| `"aosp"`       | Full AOSP image                                   | Standard emulator testing    |
| `"google"`     | Full image with Google Play Services              | Play Services integration    |

ATD images boot faster and consume less memory because they strip out UI chrome and preinstalled apps irrelevant to testing. Prefer `aosp-atd` or `google-atd` for CI pipelines.

### Running Tests

```bash
# Run on a single managed device
./gradlew pixel6Api34DebugAndroidTest

# Run on a device group (all devices in parallel if hardware allows)
./gradlew phoneTestsGroupDebugAndroidTest
./gradlew allDevicesGroupDebugAndroidTest

# With specific flavor
./gradlew pixel6Api34DevDebugAndroidTest

# Enable test sharding across devices (speeds up large suites)
./gradlew allDevicesGroupDebugAndroidTest \
    -Pandroid.experimental.androidTest.numManagedDeviceShards=2

# Generate HTML test report
./gradlew pixel6Api34DebugAndroidTest \
    --continue   # don't stop on first failure
```

Test results are written to `app/build/reports/androidTests/managedDevice/`.
