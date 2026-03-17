# Performance & Stability Guidelines

Android Vitals thresholds, performance requirements, and stability best practices.

## Android Vitals Thresholds

### Core Metrics (Google Play)

Exceeding these thresholds affects app visibility on Google Play:

| Metric | Overall Threshold | Per Phone Model | Per Watch Model |
|--------|-------------------|-----------------|-----------------|
| User-perceived crash rate | **1.09%** | 8% | 4% |
| User-perceived ANR rate | **0.47%** | 8% | 5% |
| Excessive battery usage | 1% | - | 1% |
| Excessive wake locks | 5% | - | - |

### Consequences of Exceeding Thresholds

- Reduced app visibility in Google Play
- Warning label on store listing
- Lower ranking in search results
- Negative impact on user trust

## Startup Performance

### Requirements

| Metric | Target | Maximum |
|--------|--------|---------|
| Cold start | < 1 second | 2 seconds |
| Warm start | < 500ms | 1 second |
| Hot start | < 100ms | 500ms |

### If Startup Exceeds 2 Seconds

Must provide visual feedback:
- Progress indicator
- Splash screen with animation
- Loading skeleton

### Optimization Techniques

| Technique | Impact |
|-----------|--------|
| Lazy initialization | Defer non-critical work |
| Async loading | Move I/O off main thread |
| View hierarchy optimization | Reduce layout depth |
| App Startup library | Initialize components efficiently |
| Baseline Profiles | Pre-compile hot paths |

## Rendering Performance

### Frame Rate Requirements

| Target | Frame Time | Notes |
|--------|------------|-------|
| 60 FPS | ≤ 16.67ms | Standard requirement |
| 90 FPS | ≤ 11.11ms | High refresh rate displays |
| 120 FPS | ≤ 8.33ms | Premium devices |

### Jank Detection

| Metric | Threshold | Severity |
|--------|-----------|----------|
| Slow frames | > 16ms | Warning |
| Frozen frames | > 700ms | Critical |
| Jank rate | > 1% of frames | Poor experience |

### Common Rendering Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Overdraw | Multiple layers drawn | Reduce background stacking |
| Deep hierarchy | Complex view nesting | Use ConstraintLayout, Compose |
| Main thread work | Blocking operations | Move to background thread |
| Large bitmaps | Unoptimized images | Downsample, use vector |

## ANR Prevention

### ANR Triggers

| Scenario | Timeout |
|----------|---------|
| Input dispatch | 5 seconds |
| Broadcast receiver | 10 seconds |
| Service start | 20 seconds |

### Prevention Strategies

- Never perform network calls on main thread
- Never perform database operations on main thread
- Never perform file I/O on main thread
- Use coroutines, RxJava, or other async mechanisms
- Reduce synchronized block contention

### Common ANR Causes

| Cause | Solution |
|-------|----------|
| Network on main thread | Use coroutines/RxJava |
| Database on main thread | Use Room with suspend |
| File I/O on main thread | Use Dispatchers.IO |
| Lock contention | Reduce synchronized blocks |
| Dead locks | Careful threading design |

## Battery Optimization

### Wake Lock Guidelines

| Rule | Implementation |
|------|----------------|
| Minimize duration | Release as soon as possible |
| Use appropriate type | PARTIAL_WAKE_LOCK only when needed |
| Always release | Use try-finally or lifecycle |
| Prefer WorkManager | System-managed scheduling |

### Background Restrictions

| Feature | Best Practice |
|---------|---------------|
| Background services | Use WorkManager instead |
| Location | Request only when necessary |
| Network | Batch requests, respect connectivity |
| Alarms | Use inexact alarms when possible |

### Doze and App Standby

| Mode | Behavior | Adaptation |
|------|----------|------------|
| Doze | Limited network, alarms delayed | Use FCM for high-priority |
| App Standby | Background work restricted | Use expedited WorkManager |
| Buckets | Frequency limits by usage | Design for infrequent execution |

## Memory Management

### Memory Best Practices

| Practice | Benefit |
|----------|---------|
| Avoid memory leaks | Prevent OutOfMemoryError |
| Use weak references | Allow garbage collection |
| Recycle bitmaps | Reduce memory pressure |
| Monitor heap | Profile regularly |

### Common Memory Issues

| Issue | Detection | Solution |
|-------|-----------|----------|
| Activity leak | LeakCanary | Fix lifecycle references |
| Bitmap leak | Memory profiler | Recycle, use Glide/Coil |
| Context leak | Static analysis | Use application context |
| Handler leak | Lint warning | Use WeakReference |

## StrictMode

### What StrictMode Detects

| Category | Issues |
|----------|--------|
| Thread | Disk reads/writes, network, slow calls |
| VM | Leaked objects, unsafe intents, content URI exposure |

Enable StrictMode in debug builds to detect violations during development.

## SDK Requirements

### Version Requirements

| Property | Requirement |
|----------|-------------|
| targetSdk | Latest Android SDK (Google Play requirement) |
| compileSdk | Latest Android SDK |
| minSdk | Based on target audience |

### Third-Party SDK Management

| Practice | Reason |
|----------|--------|
| Keep updated | Security fixes, compatibility |
| Audit regularly | Remove unused dependencies |
| Monitor crashes | SDKs can cause issues |
| Check permissions | SDKs may request excessive permissions |

### Non-SDK Interface Restrictions

- Don't use reflection for hidden APIs
- Use Android Studio lint to detect
- APIs may break in future versions

## Monitoring and Profiling

### Tools

| Tool | Purpose |
|------|---------|
| Android Studio Profiler | CPU, memory, network, energy |
| Android Vitals (Play Console) | Production crash/ANR data |
| Firebase Performance | Real-time performance monitoring |
| Perfetto | Advanced system tracing |
| Benchmark library | Reproducible measurements |

### Key Metrics to Track

| Metric | Tool |
|--------|------|
| Startup time | Macrobenchmark |
| Frame timing | JankStats |
| Memory usage | Memory Profiler |
| Network latency | Network Profiler |
| Battery drain | Energy Profiler |

## Performance Checklist

- [ ] Cold startup < 2 seconds
- [ ] Rendering at 60 FPS
- [ ] No StrictMode violations
- [ ] Crash rate < 1.09%
- [ ] ANR rate < 0.47%
- [ ] No memory leaks
- [ ] Background work uses WorkManager
- [ ] Wake locks properly released
- [ ] SDKs up to date
