# Navigation Patterns

iOS navigation patterns guide covering Tab navigation, Navigation Controller, and modal presentation.

## Tab-Based Navigation

For apps with 3-5 main sections:

```swift
class AppTabBarController: UITabBarController {
    override func viewDidLoad() {
        super.viewDidLoad()
        
        let homeNav = UINavigationController(rootViewController: HomeVC())
        homeNav.tabBarItem = UITabBarItem(
            title: "Home",
            image: UIImage(systemName: "house"),
            selectedImage: UIImage(systemName: "house.fill")
        )
        
        let searchNav = UINavigationController(rootViewController: SearchVC())
        searchNav.tabBarItem = UITabBarItem(
            title: "Search",
            image: UIImage(systemName: "magnifyingglass"),
            tag: 1
        )
        
        let profileNav = UINavigationController(rootViewController: ProfileVC())
        profileNav.tabBarItem = UITabBarItem(
            title: "Profile",
            image: UIImage(systemName: "person"),
            selectedImage: UIImage(systemName: "person.fill")
        )
        
        viewControllers = [homeNav, searchNav, profileNav]
    }
}
```

### Tab Bar Best Practices

| Principle | Description |
|-----------|-------------|
| Limit count | Maximum 5 tabs, use More for additional |
| Always visible | Tab bar stays visible at all navigation levels |
| State preservation | Preserve navigation state when switching tabs |
| Icon choice | Use SF Symbols, provide selected/unselected states |

## Navigation Controller

Use large titles for root views:

```swift
class ListViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Items"
        navigationController?.navigationBar.prefersLargeTitles = true
        navigationItem.largeTitleDisplayMode = .always
    }
    
    func pushDetail(_ item: Item) {
        let detail = DetailViewController(item: item)
        detail.navigationItem.largeTitleDisplayMode = .never
        navigationController?.pushViewController(detail, animated: true)
    }
}
```

### Navigation Bar Configuration

```swift
class CustomNavigationController: UINavigationController {
    override func viewDidLoad() {
        super.viewDidLoad()
        
        let appearance = UINavigationBarAppearance()
        appearance.configureWithDefaultBackground()
        
        navigationBar.standardAppearance = appearance
        navigationBar.scrollEdgeAppearance = appearance
        navigationBar.compactAppearance = appearance
    }
}
```

### Navigation Bar Buttons

```swift
override func viewDidLoad() {
    super.viewDidLoad()
    
    navigationItem.rightBarButtonItem = UIBarButtonItem(
        image: UIImage(systemName: "plus"),
        style: .plain,
        target: self,
        action: #selector(addItem)
    )
    
    navigationItem.rightBarButtonItems = [
        UIBarButtonItem(systemItem: .add, primaryAction: UIAction { _ in }),
        UIBarButtonItem(systemItem: .edit, primaryAction: UIAction { _ in })
    ]
}
```

## Modal Presentation

### Sheet Presentation

```swift
func presentEditor() {
    let editorVC = EditorViewController()
    let nav = UINavigationController(rootViewController: editorVC)
    
    editorVC.navigationItem.leftBarButtonItem = UIBarButtonItem(
        systemItem: .cancel, target: self, action: #selector(dismissEditor)
    )
    editorVC.navigationItem.rightBarButtonItem = UIBarButtonItem(
        systemItem: .done, target: self, action: #selector(saveAndDismiss)
    )
    
    if let sheet = nav.sheetPresentationController {
        sheet.detents = [.medium(), .large()]
        sheet.prefersGrabberVisible = true
        sheet.prefersScrollingExpandsWhenScrolledToEdge = false
    }
    
    present(nav, animated: true)
}
```

### Custom Detent (iOS 16+)

```swift
if let sheet = nav.sheetPresentationController {
    let customDetent = UISheetPresentationController.Detent.custom { context in
        return context.maximumDetentValue * 0.4
    }
    sheet.detents = [customDetent, .large()]
}
```

### Full Screen Presentation

```swift
func presentFullScreen() {
    let vc = FullScreenViewController()
    vc.modalPresentationStyle = .fullScreen
    vc.modalTransitionStyle = .coverVertical
    present(vc, animated: true)
}
```

## Presentation Styles

| Style | Usage |
|-------|-------|
| `.automatic` | System default (usually sheet) |
| `.pageSheet` | Card-style, parent view visible |
| `.fullScreen` | Full screen cover |
| `.overFullScreen` | Full screen with transparent background |
| `.popover` | iPad popover |

## Navigation Best Practices

1. **Back gesture** - Ensure edge swipe back always works
2. **State restoration** - Use `UIStateRestoring` to save navigation stack
3. **Depth limit** - Avoid more than 4-5 navigation levels
4. **Cancel button** - Modal views must provide a cancel option
5. **Save confirmation** - Show confirmation dialog for unsaved changes

---

*UIKit, SF Symbols, and Apple are trademarks of Apple Inc.*
