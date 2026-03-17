# Accessibility Guidelines

Comprehensive accessibility requirements for Android applications.

## Core Requirements

### Minimum Standards

| Requirement | Specification |
|-------------|---------------|
| Color contrast (text) | 4.5:1 minimum |
| Color contrast (large text) | 3:1 minimum |
| Color contrast (UI components) | 3:1 minimum |
| Touch targets | 48 × 48dp minimum |
| Content descriptions | All interactive elements |
| Focus indicators | Clearly visible |
| Screen reader support | Proper semantics |

## Content Labels

### contentDescription

Use for non-text interactive elements.

**When to use:**
- ImageView, ImageButton
- CheckBox, Switch (state description)
- Custom drawable views
- Icons that convey meaning

**When NOT to use:**
- TextView (uses text content automatically)
- Decorative images (set to null)
- Elements with labelFor relationship

### android:hint

Use for editable text fields to show placeholder text.

**Important**: Don't use contentDescription on EditText—it interferes with accessibility services.

### android:labelFor

Link labels to input fields by setting labelFor on the TextView to reference the EditText ID.

## Label Best Practices

### Do's

| Practice | Example |
|----------|---------|
| Be concise | "Save" not "Click here to save" |
| Describe action/purpose | "Delete message" |
| Be unique in context | "Delete item 3" not just "Delete" |
| Update dynamically | "Pause" ↔ "Play" based on state |

### Don'ts

| Avoid | Reason |
|-------|--------|
| Include element type | TalkBack announces "button" automatically |
| Say "button", "image", etc. | Redundant with accessibility info |
| Use "click" or "tap" | Input method varies |
| Leave empty/generic | "Button" or "Image" is unhelpful |

### Examples

| Bad | Good |
|-----|------|
| "Save button" | "Save" |
| "Click here to submit" | "Submit" |
| "Image" | "Profile photo of John" |
| "Button 1" | "Add to cart" |

## Focus and Navigation

### Focus Groups

Group related elements using `screenReaderFocusable="true"` on the container and `focusable="false"` on child elements. TalkBack will announce all children's content in a single utterance.

### Headings

Mark section headers with `accessibilityHeading="true"`. Users can navigate between headings for quick scanning.

### Pane Titles

Identify screen regions with `accessibilityPaneTitle`. Accessibility services announce pane changes.

### Focus Order

- Natural reading order (top-to-bottom, start-to-end)
- Use `accessibilityTraversalBefore/After` for custom order
- Ensure all interactive elements are focusable
- Skip decorative elements

## Decorative Elements

Skip elements that don't convey information:
- Set `contentDescription="@null"`
- Or set `importantForAccessibility="no"`

## Custom Accessibility Actions

### Adding Actions

Provide alternatives for gesture-based interactions using `ViewCompat.addAccessibilityAction()`. This exposes swipe actions to accessibility services.

### Replacing Action Labels

Make default actions more descriptive using `ViewCompat.replaceAccessibilityAction()`. Example: "Double tap and hold to add to favorites" instead of generic "long press".

## Color and Visual Cues

### Don't Rely on Color Alone

Combine color with other indicators:

| Information | Color + Alternative |
|-------------|---------------------|
| Error state | Red + error icon + text |
| Success | Green + checkmark + text |
| Required field | Red asterisk + "Required" label |
| Selected item | Highlight + checkmark + bold |
| Link text | Blue + underline |

### Contrast Testing

Use tools to verify contrast:
- Android Accessibility Scanner
- Contrast Checker plugins
- Manual calculation: (L1 + 0.05) / (L2 + 0.05)

## Touch Targets

### Minimum Sizes

| Element | Minimum | Recommended |
|---------|---------|-------------|
| Standard | 48 × 48dp | 48 × 48dp |
| Primary actions | 48 × 48dp | 56 × 56dp |
| Kids apps | 56 × 56dp | 64 × 64dp |

### Spacing

- Minimum 8dp between adjacent touch targets
- Visual element can be smaller if touch area is adequate (use padding)

## Screen Reader Announcements

### Live Regions

Announce dynamic content changes using `accessibilityLiveRegion`:

| Mode | Usage |
|------|-------|
| polite | Announces when user is idle |
| assertive | Interrupts current speech |
| none | No automatic announcements |

### Custom Announcements

Use `announceForAccessibility()` sparingly—prefer live regions.

## Keyboard and Hardware Navigation

### Focus Indicators

- Visible focus state for all interactive elements
- Don't remove default focus indicators
- Custom focus: 2dp+ border or background change

### Keyboard Shortcuts

- Support Tab navigation
- Enter/Space for activation
- Arrow keys for lists/grids
- Escape for dismissal

## Testing Accessibility

### Manual Testing

1. **TalkBack**: Navigate entire app with screen reader
2. **Switch Access**: Test with switch navigation
3. **Keyboard**: Navigate with external keyboard only
4. **Magnification**: Test with zoom enabled
5. **Large text**: Test with 200% font scale
6. **High contrast**: Test with high contrast mode

### Automated Testing

| Tool | Purpose |
|------|---------|
| Accessibility Scanner | On-device scanning |
| Espresso Accessibility Checks | Automated UI tests |
| Lint checks | Static analysis |

### Checklist

- [ ] All interactive elements have descriptions
- [ ] Touch targets are 48dp minimum
- [ ] Color contrast meets requirements
- [ ] Focus order is logical
- [ ] Headings are properly marked
- [ ] Custom actions have descriptive labels
- [ ] Live regions announce important changes
- [ ] Keyboard navigation works
- [ ] Works with TalkBack enabled
- [ ] Works with large text (200%)
