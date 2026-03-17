# UIKit Components

Common UIKit components guide covering UIStackView, buttons, alerts, search, and context menus.

## UIStackView

Stack views simplify auto layout for linear arrangements:

```swift
class FormViewController: UIViewController {
    private let mainStack = UIStackView()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        mainStack.axis = .vertical
        mainStack.spacing = 16
        mainStack.alignment = .fill
        mainStack.distribution = .fill
        
        view.addSubview(mainStack)
        mainStack.snp.makeConstraints { make in
            make.top.equalTo(view.safeAreaLayoutGuide).offset(20)
            make.leading.trailing.equalToSuperview().inset(16)
        }
        
        let headerStack = UIStackView()
        headerStack.axis = .horizontal
        headerStack.spacing = 12
        headerStack.alignment = .center
        
        let avatarView = UIImageView()
        avatarView.snp.makeConstraints { make in
            make.size.equalTo(48)
        }
        
        let labelStack = UIStackView()
        labelStack.axis = .vertical
        labelStack.spacing = 4
        labelStack.addArrangedSubview(titleLabel)
        labelStack.addArrangedSubview(subtitleLabel)
        
        headerStack.addArrangedSubview(avatarView)
        headerStack.addArrangedSubview(labelStack)
        
        mainStack.addArrangedSubview(headerStack)
        mainStack.addArrangedSubview(contentView)
        mainStack.addArrangedSubview(actionButton)
        
        mainStack.setCustomSpacing(24, after: headerStack)
    }
}
```

### StackView Properties

| Property | Options | Usage |
|----------|---------|-------|
| `axis` | `.horizontal`, `.vertical` | Layout direction |
| `distribution` | `.fill`, `.fillEqually`, `.fillProportionally`, `.equalSpacing`, `.equalCentering` | Space distribution |
| `alignment` | `.fill`, `.leading`, `.center`, `.trailing` | Cross-axis alignment |
| `spacing` | CGFloat | Uniform spacing |
| `setCustomSpacing(_:after:)` | - | Variable spacing |

## UIButton.Configuration (iOS 15+)

```swift
let primaryButton = UIButton(type: .system)
primaryButton.configuration = .filled()
primaryButton.setTitle("Continue", for: .normal)

let secondaryButton = UIButton(type: .system)
secondaryButton.configuration = .tinted()
secondaryButton.setTitle("Save for Later", for: .normal)

let destructiveButton = UIButton(type: .system)
destructiveButton.configuration = .plain()
destructiveButton.setTitle("Remove", for: .normal)
destructiveButton.tintColor = .systemRed
```

### Custom Button Configuration

```swift
var config = UIButton.Configuration.filled()
config.title = "Add to Cart"
config.image = UIImage(systemName: "cart.badge.plus")
config.imagePadding = 8
config.cornerStyle = .capsule
config.baseBackgroundColor = .systemBlue
config.baseForegroundColor = .white
let cartButton = UIButton(configuration: config)
```

### Button State Handling

```swift
var config = UIButton.Configuration.filled()
config.titleTextAttributesTransformer = UIConfigurationTextAttributesTransformer { incoming in
    var outgoing = incoming
    outgoing.font = .boldSystemFont(ofSize: 16)
    return outgoing
}

config.configurationUpdateHandler = { button in
    var config = button.configuration
    config?.showsActivityIndicator = button.isSelected
    button.configuration = config
}
```

## UIAlertController

### Alert

```swift
func confirmDeletion() {
    let alert = UIAlertController(
        title: "Remove Item?",
        message: "This cannot be undone.",
        preferredStyle: .alert
    )
    alert.addAction(UIAlertAction(title: "Remove", style: .destructive) { _ in
        self.performDeletion()
    })
    alert.addAction(UIAlertAction(title: "Cancel", style: .cancel))
    present(alert, animated: true)
}
```

### Action Sheet

```swift
func showOptions() {
    let sheet = UIAlertController(title: nil, message: nil, preferredStyle: .actionSheet)
    sheet.addAction(UIAlertAction(title: "Share", style: .default) { _ in })
    sheet.addAction(UIAlertAction(title: "Edit", style: .default) { _ in })
    sheet.addAction(UIAlertAction(title: "Delete", style: .destructive) { _ in })
    sheet.addAction(UIAlertAction(title: "Cancel", style: .cancel))
    
    if let popover = sheet.popoverPresentationController {
        popover.sourceView = optionsButton
        popover.sourceRect = optionsButton.bounds
    }
    
    present(sheet, animated: true)
}
```

### Alert with Text Field

```swift
func showInputAlert() {
    let alert = UIAlertController(
        title: "Rename",
        message: "Enter a new name",
        preferredStyle: .alert
    )
    
    alert.addTextField { textField in
        textField.placeholder = "Name"
        textField.autocapitalizationType = .words
    }
    
    alert.addAction(UIAlertAction(title: "Save", style: .default) { _ in
        if let name = alert.textFields?.first?.text {
            self.rename(to: name)
        }
    })
    alert.addAction(UIAlertAction(title: "Cancel", style: .cancel))
    
    present(alert, animated: true)
}
```

## UISearchController

```swift
class SearchableListVC: UIViewController, UISearchResultsUpdating {
    private let searchController = UISearchController(searchResultsController: nil)
    private var allItems: [Item] = []
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupSearch()
    }
    
    private func setupSearch() {
        searchController.searchResultsUpdater = self
        searchController.obscuresBackgroundDuringPresentation = false
        searchController.searchBar.placeholder = "Search"
        navigationItem.searchController = searchController
        definesPresentationContext = true
    }
    
    func updateSearchResults(for searchController: UISearchController) {
        let query = searchController.searchBar.text ?? ""
        let filtered = query.isEmpty ? allItems : allItems.filter {
            $0.title.localizedCaseInsensitiveContains(query)
        }
        updateItems(filtered)
    }
}
```

### Search Bar Configuration

```swift
searchController.searchBar.scopeButtonTitles = ["All", "Recent", "Favorites"]
searchController.searchBar.showsScopeBar = true
searchController.searchBar.delegate = self

extension SearchableListVC: UISearchBarDelegate {
    func searchBar(_ searchBar: UISearchBar, selectedScopeButtonIndexDidChange selectedScope: Int) {
        filterContent(scope: selectedScope)
    }
}
```

## UIContextMenuInteraction

```swift
extension PhotoCell: UIContextMenuInteractionDelegate {
    func contextMenuInteraction(
        _ interaction: UIContextMenuInteraction,
        configurationForMenuAtLocation location: CGPoint
    ) -> UIContextMenuConfiguration? {
        UIContextMenuConfiguration(identifier: nil, previewProvider: nil) { _ in
            let share = UIAction(
                title: "Share",
                image: UIImage(systemName: "square.and.arrow.up")
            ) { _ in }
            
            let favorite = UIAction(
                title: "Favorite",
                image: UIImage(systemName: "heart")
            ) { _ in }
            
            let delete = UIAction(
                title: "Delete",
                image: UIImage(systemName: "trash"),
                attributes: .destructive
            ) { _ in }
            
            return UIMenu(children: [share, favorite, delete])
        }
    }
}
```

### Context Menu with Preview

```swift
func contextMenuInteraction(
    _ interaction: UIContextMenuInteraction,
    configurationForMenuAtLocation location: CGPoint
) -> UIContextMenuConfiguration? {
    UIContextMenuConfiguration(
        identifier: itemID as NSCopying,
        previewProvider: { [weak self] in
            return self?.makePreviewController()
        },
        actionProvider: { _ in
            return self.makeMenu()
        }
    )
}

func contextMenuInteraction(
    _ interaction: UIContextMenuInteraction,
    willPerformPreviewActionForMenuWith configuration: UIContextMenuConfiguration,
    animator: UIContextMenuInteractionCommitAnimating
) {
    animator.addCompletion {
        self.showDetail()
    }
}
```

### CollectionView Context Menu

```swift
func collectionView(
    _ collectionView: UICollectionView,
    contextMenuConfigurationForItemAt indexPath: IndexPath,
    point: CGPoint
) -> UIContextMenuConfiguration? {
    let item = dataSource.itemIdentifier(for: indexPath)
    return UIContextMenuConfiguration(identifier: indexPath as NSCopying, previewProvider: nil) { _ in
        return self.makeMenu(for: item)
    }
}
```

---

*UIKit and Apple are trademarks of Apple Inc.*
