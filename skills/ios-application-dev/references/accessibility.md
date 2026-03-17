# Accessibility

iOS accessibility guide covering Dynamic Type, semantic colors, VoiceOver, and motion adaptation.

## Dynamic Type

### Using System Fonts

```swift
private func setupLabels() {
    let titleLabel = UILabel()
    titleLabel.font = .preferredFont(forTextStyle: .headline)
    titleLabel.adjustsFontForContentSizeCategory = true
    
    let bodyLabel = UILabel()
    bodyLabel.font = .preferredFont(forTextStyle: .body)
    bodyLabel.adjustsFontForContentSizeCategory = true
    bodyLabel.numberOfLines = 0
}
```

### Custom Font Scaling

```swift
extension UIFont {
    static func scaled(_ name: String, size: CGFloat, for style: TextStyle) -> UIFont {
        guard let font = UIFont(name: name, size: size) else {
            return .preferredFont(forTextStyle: style)
        }
        return UIFontMetrics(forTextStyle: style).scaledFont(for: font)
    }
}

let customFont = UIFont.scaled("Avenir-Medium", size: 16, for: .body)
```

### Text Style Reference

| Style | Default Size | Usage |
|-------|--------------|-------|
| `.largeTitle` | 34pt | Screen titles |
| `.title1` | 28pt | Primary headings |
| `.title2` | 22pt | Secondary headings |
| `.title3` | 20pt | Tertiary headings |
| `.headline` | 17pt (semibold) | Important information |
| `.body` | 17pt | Body text |
| `.callout` | 16pt | Explanatory text |
| `.subheadline` | 15pt | Subtitles |
| `.footnote` | 13pt | Footnotes |
| `.caption1` | 12pt | Labels |
| `.caption2` | 11pt | Small labels |

### Adapting Layout for Large Text

```swift
override func traitCollectionDidChange(_ previous: UITraitCollection?) {
    super.traitCollectionDidChange(previous)
    
    let isLargeText = traitCollection.preferredContentSizeCategory.isAccessibilityCategory
    contentStack.axis = isLargeText ? .vertical : .horizontal
    
    if isLargeText {
        iconImageView.snp.remakeConstraints { make in
            make.size.equalTo(64)
        }
    } else {
        iconImageView.snp.remakeConstraints { make in
            make.size.equalTo(44)
        }
    }
}
```

## Semantic Colors

Use system semantic colors for automatic Dark Mode adaptation:

```swift
view.backgroundColor = .systemBackground
containerView.backgroundColor = .secondarySystemBackground
cardView.backgroundColor = .tertiarySystemBackground

titleLabel.textColor = .label
subtitleLabel.textColor = .secondaryLabel
hintLabel.textColor = .tertiaryLabel
placeholderLabel.textColor = .placeholderText

separatorView.backgroundColor = .separator
borderView.layer.borderColor = UIColor.separator.cgColor
```

### System Color Reference

| Color | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `.systemBackground` | White | Black | Main background |
| `.secondarySystemBackground` | Light gray | Dark gray | Card/grouped background |
| `.tertiarySystemBackground` | Lighter gray | Medium gray | Nested content background |
| `.label` | Black | White | Primary text |
| `.secondaryLabel` | Gray | Light gray | Secondary text |
| `.tertiaryLabel` | Light gray | Dark gray | Auxiliary text |

### Custom Color Adaptation

```swift
extension UIColor {
    static let customAccent = UIColor { traitCollection in
        switch traitCollection.userInterfaceStyle {
        case .dark:
            return UIColor(red: 0.4, green: 0.8, blue: 1.0, alpha: 1.0)
        default:
            return UIColor(red: 0.0, green: 0.5, blue: 0.8, alpha: 1.0)
        }
    }
}
```

## VoiceOver

### Basic Labels

```swift
let cartButton = UIButton(type: .system)
cartButton.setImage(UIImage(systemName: "cart.badge.plus"), for: .normal)
cartButton.accessibilityLabel = "Add to cart"

let ratingView = UIView()
ratingView.accessibilityLabel = "Rating: 4 out of 5 stars"

let closeButton = UIButton()
closeButton.accessibilityLabel = "Close"
closeButton.accessibilityHint = "Dismisses this dialog"
```

### Custom Accessibility

```swift
class ProductCell: UICollectionViewCell {
    override var accessibilityLabel: String? {
        get {
            return "\(product.name), \(product.price), \(product.isAvailable ? "In stock" : "Out of stock")"
        }
        set {}
    }
    
    override var accessibilityTraits: UIAccessibilityTraits {
        get {
            var traits: UIAccessibilityTraits = .button
            if product.isSelected {
                traits.insert(.selected)
            }
            return traits
        }
        set {}
    }
}
```

### Accessibility Container

```swift
class CustomContainerView: UIView {
    override var isAccessibilityElement: Bool {
        get { false }
        set {}
    }
    
    override var accessibilityElements: [Any]? {
        get {
            return [titleLabel, actionButton, detailLabel]
        }
        set {}
    }
}
```

### VoiceOver Notifications

```swift
func didLoadContent() {
    UIAccessibility.post(notification: .screenChanged, argument: headerLabel)
}

func didUpdateStatus() {
    UIAccessibility.post(notification: .announcement, argument: "Download complete")
}
```

## Reduce Motion

```swift
func animateTransition() {
    let duration: TimeInterval = UIAccessibility.isReduceMotionEnabled ? 0 : 0.3
    UIView.animate(withDuration: duration) {
        self.cardView.alpha = 1
    }
}

func showPopup() {
    if UIAccessibility.isReduceMotionEnabled {
        popupView.alpha = 1
    } else {
        popupView.transform = CGAffineTransform(scaleX: 0.8, y: 0.8)
        popupView.alpha = 0
        UIView.animate(withDuration: 0.3, delay: 0, usingSpringWithDamping: 0.7, initialSpringVelocity: 0) {
            self.popupView.transform = .identity
            self.popupView.alpha = 1
        }
    }
}
```

### Observing Setting Changes

```swift
NotificationCenter.default.addObserver(
    self,
    selector: #selector(reduceMotionChanged),
    name: UIAccessibility.reduceMotionStatusDidChangeNotification,
    object: nil
)

@objc func reduceMotionChanged() {
    updateAnimationSettings()
}
```

## Accessibility Checklist

### Basic Requirements
- [ ] All icon buttons have `accessibilityLabel`
- [ ] Custom controls have correct `accessibilityTraits`
- [ ] Images have `accessibilityLabel` or marked as decorative
- [ ] Forms have clear error messages

### Dynamic Type
- [ ] Using `preferredFont(forTextStyle:)`
- [ ] Set `adjustsFontForContentSizeCategory = true`
- [ ] Layout adapts at accessibility sizes
- [ ] Text is not truncated

### Color Contrast
- [ ] Body text contrast >= 4.5:1
- [ ] Large text contrast >= 3:1
- [ ] Information not conveyed by color alone

### Motion
- [ ] Respect Reduce Motion setting
- [ ] No flashing or rapid animation
- [ ] Auto-playing animations can be paused

### Interaction
- [ ] Touch targets >= 44x44pt
- [ ] Gestures have alternative actions
- [ ] Timeouts can be extended

---

*UIKit, VoiceOver, Dynamic Type, and Apple are trademarks of Apple Inc.*
