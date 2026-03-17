# Layout System

iOS layout system guide covering touch targets, safe areas, UICollectionView, and Compositional Layout.

## Touch Targets

Interactive elements need adequate tap areas. The recommended minimum is 44x44 points.

```swift
let actionButton = UIButton(type: .system)
actionButton.setTitle("Submit", for: .normal)
view.addSubview(actionButton)

actionButton.snp.makeConstraints { make in
    make.height.greaterThanOrEqualTo(44)
    make.leading.trailing.equalToSuperview().inset(16)
    make.bottom.equalTo(view.safeAreaLayoutGuide).offset(-16)
}
```

Use 8-point increments for spacing (8, 16, 24, 32, 40, 48) to maintain visual consistency.

## Safe Area

Always constrain content to the safe area to avoid the notch, Dynamic Island, and home indicator.

```swift
class MainViewController: UIViewController {
    private let contentStack = UIStackView()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        
        contentStack.axis = .vertical
        contentStack.spacing = 16
        view.addSubview(contentStack)
        
        contentStack.snp.makeConstraints { make in
            make.top.bottom.equalTo(view.safeAreaLayoutGuide)
            make.leading.trailing.equalTo(view.safeAreaLayoutGuide).inset(16)
        }
    }
}
```

## UICollectionView with Diffable Data Source

```swift
class ItemsViewController: UIViewController {
    enum Section { case main }
    
    private var collectionView: UICollectionView!
    private var dataSource: UICollectionViewDiffableDataSource<Section, Item>!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupCollectionView()
        configureDataSource()
    }
    
    private func setupCollectionView() {
        var config = UICollectionLayoutListConfiguration(appearance: .insetGrouped)
        config.trailingSwipeActionsConfigurationProvider = { [weak self] indexPath in
            self?.makeSwipeActions(for: indexPath)
        }
        
        let layout = UICollectionViewCompositionalLayout.list(using: config)
        collectionView = UICollectionView(frame: .zero, collectionViewLayout: layout)
        
        view.addSubview(collectionView)
        collectionView.snp.makeConstraints { make in
            make.edges.equalToSuperview()
        }
    }
    
    private func configureDataSource() {
        let cellRegistration = UICollectionView.CellRegistration<UICollectionViewListCell, Item> { 
            cell, indexPath, item in
            var content = cell.defaultContentConfiguration()
            content.text = item.title
            content.secondaryText = item.subtitle
            cell.contentConfiguration = content
        }
        
        dataSource = UICollectionViewDiffableDataSource(collectionView: collectionView) { 
            collectionView, indexPath, item in
            collectionView.dequeueConfiguredReusableCell(
                using: cellRegistration, for: indexPath, item: item
            )
        }
    }
    
    func updateItems(_ items: [Item]) {
        var snapshot = NSDiffableDataSourceSnapshot<Section, Item>()
        snapshot.appendSections([.main])
        snapshot.appendItems(items)
        dataSource.apply(snapshot)
    }
}
```

## Grid Layout

```swift
private func createGridLayout() -> UICollectionViewLayout {
    let itemSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1/3),
        heightDimension: .fractionalHeight(1.0)
    )
    let item = NSCollectionLayoutItem(layoutSize: itemSize)
    item.contentInsets = NSDirectionalEdgeInsets(top: 2, leading: 2, bottom: 2, trailing: 2)
    
    let groupSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .fractionalWidth(1/3)
    )
    let group = NSCollectionLayoutGroup.horizontal(layoutSize: groupSize, subitems: [item])
    
    let section = NSCollectionLayoutSection(group: group)
    return UICollectionViewCompositionalLayout(section: section)
}
```

## Sectioned List with Headers

```swift
class CategorizedListVC: UIViewController {
    enum Section: Hashable {
        case favorites, recent, all
    }
    
    private var dataSource: UICollectionViewDiffableDataSource<Section, Item>!
    
    private func setupCollectionView() {
        var config = UICollectionLayoutListConfiguration(appearance: .insetGrouped)
        config.headerMode = .supplementary
        
        let layout = UICollectionViewCompositionalLayout.list(using: config)
        collectionView = UICollectionView(frame: .zero, collectionViewLayout: layout)
    }
    
    private func configureDataSource() {
        let cellRegistration = UICollectionView.CellRegistration<UICollectionViewListCell, Item> { 
            cell, indexPath, item in
            var content = cell.defaultContentConfiguration()
            content.text = item.title
            cell.contentConfiguration = content
        }
        
        let headerRegistration = UICollectionView.SupplementaryRegistration<UICollectionViewListCell>(
            elementKind: UICollectionView.elementKindSectionHeader
        ) { [weak self] header, elementKind, indexPath in
            guard let section = self?.dataSource.sectionIdentifier(for: indexPath.section) else { return }
            var content = header.defaultContentConfiguration()
            content.text = self?.title(for: section)
            header.contentConfiguration = content
        }
        
        dataSource = UICollectionViewDiffableDataSource(collectionView: collectionView) { 
            collectionView, indexPath, item in
            collectionView.dequeueConfiguredReusableCell(using: cellRegistration, for: indexPath, item: item)
        }
        
        dataSource.supplementaryViewProvider = { collectionView, kind, indexPath in
            collectionView.dequeueConfiguredReusableSupplementary(using: headerRegistration, for: indexPath)
        }
    }
    
    func applySnapshot(favorites: [Item], recent: [Item], all: [Item]) {
        var snapshot = NSDiffableDataSourceSnapshot<Section, Item>()
        if !favorites.isEmpty {
            snapshot.appendSections([.favorites])
            snapshot.appendItems(favorites, toSection: .favorites)
        }
        if !recent.isEmpty {
            snapshot.appendSections([.recent])
            snapshot.appendItems(recent, toSection: .recent)
        }
        snapshot.appendSections([.all])
        snapshot.appendItems(all, toSection: .all)
        dataSource.apply(snapshot)
    }
}
```

## Spacing Guidelines

| Spacing | Usage |
|---------|-------|
| 8pt | Compact element spacing |
| 16pt | Standard padding |
| 24pt | Section spacing |
| 32pt | Large section separation |
| 48pt | Screen margins (large screens) |

---

*UIKit and Apple are trademarks of Apple Inc. SnapKit is a trademark of its respective owners.*
