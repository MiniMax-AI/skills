# System Integration

iOS system integration guide covering permissions, location, sharing, app lifecycle, and haptic feedback.

## Permission Requests

Request permissions contextually, not at launch:

```swift
import AVFoundation

@objc func openCamera() {
    AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
        DispatchQueue.main.async {
            if granted {
                self?.showCameraInterface()
            } else {
                self?.showPermissionDeniedAlert()
            }
        }
    }
}
```

### Photo Library

```swift
import Photos

func requestPhotoAccess() {
    PHPhotoLibrary.requestAuthorization(for: .readWrite) { status in
        DispatchQueue.main.async {
            switch status {
            case .authorized, .limited:
                self.showPhotoPicker()
            case .denied, .restricted:
                self.showSettingsAlert()
            default:
                break
            }
        }
    }
}
```

### Microphone

```swift
func requestMicrophoneAccess() {
    AVAudioSession.sharedInstance().requestRecordPermission { granted in
        DispatchQueue.main.async {
            if granted {
                self.startRecording()
            }
        }
    }
}
```

### Notifications

```swift
import UserNotifications

func requestNotificationPermission() {
    UNUserNotificationCenter.current().requestAuthorization(
        options: [.alert, .badge, .sound]
    ) { granted, error in
        DispatchQueue.main.async {
            if granted {
                self.registerForRemoteNotifications()
            }
        }
    }
}
```

## Location Button

For one-time location access without persistent permission:

```swift
import CoreLocationUI

class StoreFinderVC: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        
        let locationBtn = CLLocationButton()
        locationBtn.icon = .arrowFilled
        locationBtn.label = .currentLocation
        locationBtn.cornerRadius = 20
        locationBtn.addTarget(self, action: #selector(findNearby), for: .touchUpInside)
        
        view.addSubview(locationBtn)
        locationBtn.snp.makeConstraints { make in
            make.centerX.equalToSuperview()
            make.bottom.equalTo(view.safeAreaLayoutGuide).offset(-24)
        }
    }
}
```

### Core Location

```swift
import CoreLocation

class LocationManager: NSObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    
    func requestLocation() {
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.requestWhenInUseAuthorization()
    }
    
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        switch manager.authorizationStatus {
        case .authorizedWhenInUse, .authorizedAlways:
            manager.requestLocation()
        case .denied:
            showLocationDeniedAlert()
        default:
            break
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        handleLocation(location)
    }
}
```

## Share Sheet

```swift
@objc func shareContent() {
    let items: [Any] = [contentURL, contentImage].compactMap { $0 }
    let activityVC = UIActivityViewController(activityItems: items, applicationActivities: nil)
    
    if let popover = activityVC.popoverPresentationController {
        popover.sourceView = shareButton
        popover.sourceRect = shareButton.bounds
    }
    
    present(activityVC, animated: true)
}
```

### Custom Share Items

```swift
class ShareItem: NSObject, UIActivityItemSource {
    let title: String
    let url: URL
    
    init(title: String, url: URL) {
        self.title = title
        self.url = url
    }
    
    func activityViewControllerPlaceholderItem(_ activityViewController: UIActivityViewController) -> Any {
        return url
    }
    
    func activityViewController(_ activityViewController: UIActivityViewController, itemForActivityType activityType: UIActivity.ActivityType?) -> Any? {
        return url
    }
    
    func activityViewController(_ activityViewController: UIActivityViewController, subjectForActivityType activityType: UIActivity.ActivityType?) -> String {
        return title
    }
}
```

### Excluding Activities

```swift
let activityVC = UIActivityViewController(activityItems: items, applicationActivities: nil)
activityVC.excludedActivityTypes = [
    .addToReadingList,
    .assignToContact,
    .print
]
```

## App Lifecycle

```swift
class PlayerViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        
        NotificationCenter.default.addObserver(
            self, selector: #selector(onBackground),
            name: UIApplication.didEnterBackgroundNotification, object: nil
        )
        NotificationCenter.default.addObserver(
            self, selector: #selector(onForeground),
            name: UIApplication.willEnterForegroundNotification, object: nil
        )
        NotificationCenter.default.addObserver(
            self, selector: #selector(onTerminate),
            name: UIApplication.willTerminateNotification, object: nil
        )
    }
    
    @objc private func onBackground() { 
        saveState()
        pausePlayback()
    }
    
    @objc private func onForeground() { 
        restoreState()
        resumePlayback()
    }
    
    @objc private func onTerminate() {
        saveState()
    }
}
```

### Scene Lifecycle (iOS 13+)

```swift
class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    func sceneDidBecomeActive(_ scene: UIScene) {
        // Resume tasks
    }
    
    func sceneWillResignActive(_ scene: UIScene) {
        // Pause tasks
    }
    
    func sceneDidEnterBackground(_ scene: UIScene) {
        // Save state
    }
    
    func sceneWillEnterForeground(_ scene: UIScene) {
        // Prepare UI
    }
}
```

### State Preservation

```swift
class ViewController: UIViewController {
    override func encodeRestorableState(with coder: NSCoder) {
        super.encodeRestorableState(with: coder)
        coder.encode(currentItemID, forKey: "currentItemID")
    }
    
    override func decodeRestorableState(with coder: NSCoder) {
        super.decodeRestorableState(with: coder)
        if let itemID = coder.decodeObject(forKey: "currentItemID") as? String {
            loadItem(itemID)
        }
    }
}
```

## Haptic Feedback

```swift
func onTaskComplete() {
    UINotificationFeedbackGenerator().notificationOccurred(.success)
}

func onError() {
    UINotificationFeedbackGenerator().notificationOccurred(.error)
}

func onWarning() {
    UINotificationFeedbackGenerator().notificationOccurred(.warning)
}

func onSelection() {
    UISelectionFeedbackGenerator().selectionChanged()
}

func onImpact() {
    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
}
```

### Impact Styles

| Style | Usage |
|-------|-------|
| `.light` | Subtle feedback, small UI changes |
| `.medium` | Standard feedback, button presses |
| `.heavy` | Strong feedback, significant actions |
| `.soft` | Gentle feedback, background changes |
| `.rigid` | Sharp feedback, collisions |

### Prepared Feedback

For time-critical haptics, prepare the generator in advance:

```swift
class DraggableView: UIView {
    private let impactGenerator = UIImpactFeedbackGenerator(style: .medium)
    
    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        super.touchesBegan(touches, with: event)
        impactGenerator.prepare()
    }
    
    func didSnapToPosition() {
        impactGenerator.impactOccurred()
    }
}
```

## Deep Linking

### URL Schemes

```swift
// In AppDelegate or SceneDelegate
func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey: Any] = [:]) -> Bool {
    guard let components = URLComponents(url: url, resolvingAgainstBaseURL: true) else {
        return false
    }
    
    switch components.host {
    case "item":
        if let itemID = components.queryItems?.first(where: { $0.name == "id" })?.value {
            navigateToItem(itemID)
            return true
        }
    default:
        break
    }
    
    return false
}
```

### Universal Links

```swift
func application(_ application: UIApplication, continue userActivity: NSUserActivity, restorationHandler: @escaping ([UIUserActivityRestoring]?) -> Void) -> Bool {
    guard userActivity.activityType == NSUserActivityTypeBrowsingWeb,
          let url = userActivity.webpageURL else {
        return false
    }
    
    return handleUniversalLink(url)
}
```

## Background Tasks

```swift
import BackgroundTasks

func registerBackgroundTasks() {
    BGTaskScheduler.shared.register(
        forTaskWithIdentifier: "com.app.refresh",
        using: nil
    ) { task in
        self.handleAppRefresh(task: task as! BGAppRefreshTask)
    }
}

func scheduleAppRefresh() {
    let request = BGAppRefreshTaskRequest(identifier: "com.app.refresh")
    request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60)
    
    do {
        try BGTaskScheduler.shared.submit(request)
    } catch {
        print("Could not schedule app refresh: \(error)")
    }
}

func handleAppRefresh(task: BGAppRefreshTask) {
    scheduleAppRefresh()
    
    let operation = RefreshOperation()
    
    task.expirationHandler = {
        operation.cancel()
    }
    
    operation.completionBlock = {
        task.setTaskCompleted(success: !operation.isCancelled)
    }
    
    OperationQueue.main.addOperation(operation)
}
```

---

*UIKit, Core Location, and Apple are trademarks of Apple Inc.*
