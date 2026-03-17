# Adaptive Screens Guidelines

Requirements for large screens, tablets, foldables, and multi-window support.

## Adaptive Quality Tiers

Google defines three progressive quality tiers for adaptive apps:

### Tier 3: Adaptive Ready (Basic)

Minimum requirements for all apps:

| Requirement | Description |
|-------------|-------------|
| Full screen | App fills display, no letterboxing |
| Configuration changes | Handles rotation, folding, resizing |
| Multi-window | Supports split-screen mode |
| Basic input | Keyboard, mouse, trackpad support |

### Tier 2: Adaptive Optimized (Better)

Enhanced experience:

| Requirement | Description |
|-------------|-------------|
| Layout optimization | Responsive layouts for all sizes |
| Enhanced input | Full keyboard shortcuts, mouse hover states |
| Continuity | Seamless state preservation |

### Tier 1: Adaptive Differentiated (Best)

Device-specific excellence:

| Requirement | Description |
|-------------|-------------|
| Multitasking | Drag and drop, activity embedding |
| Foldable postures | Table-top mode, book mode support |
| Stylus | Full stylus input support |
| Desktop | Windowed mode optimization |

## Screen Size Classes

### Width-Based Classes

| Class | Width | Typical Devices |
|-------|-------|-----------------|
| Compact | < 600dp | Phone portrait |
| Medium | 600-840dp | Tablet portrait, phone landscape |
| Expanded | > 840dp | Tablet landscape, desktop |

### Layout Strategies

| Screen Class | Navigation | Content Layout |
|--------------|------------|----------------|
| Compact | Bottom nav | Single pane |
| Medium | Nav rail | List-detail (optional) |
| Expanded | Nav drawer/rail | List-detail, multi-pane |

## Configuration Changes

### Must Handle

| Change | Trigger |
|--------|---------|
| Rotation | Device rotated |
| Fold/Unfold | Foldable state change |
| Window resize | Multi-window adjustment |
| Split screen | Enter/exit split mode |
| Keyboard | External keyboard attach/detach |

### Configuration Handling

| Approach | Description |
|----------|-------------|
| Let system handle | Default, activity recreated |
| Handle manually | Declare configChanges, implement onConfigurationChanged |

### State Preservation

- Use ViewModel for UI state
- Use SavedStateHandle for process death
- Test with "Don't keep activities" enabled

## Multi-Window Support

### Requirements

| Feature | Status |
|---------|--------|
| resizeableActivity | true (default API 24+) |
| Minimum size | Support 220dp width |
| State handling | Preserve across resize |

### Best Practices

- Don't assume full-screen ownership
- Handle onConfigurationChanged gracefully
- Test at minimum supported size
- Support free-form windows (desktop mode)

## Foldable Devices

### Postures

| Posture | Description | Use Case |
|---------|-------------|----------|
| Flat | Fully open | Normal tablet use |
| Half-opened (tabletop) | Hinged at ~90° horizontal | Video calls, media |
| Half-opened (book) | Hinged at ~90° vertical | Reading, productivity |
| Folded | Closed | Compact phone mode |

### Design Considerations

- Avoid placing interactive elements on the fold
- Consider separate content for each screen segment
- Support continuity when fold state changes
- Use WindowInfoTracker to detect fold state

## External Input Devices

### Keyboard Support

| Requirement | Implementation |
|-------------|----------------|
| Tab navigation | Focusable elements in order |
| Enter/Space | Activates focused element |
| Arrow keys | Navigate lists, grids |
| Shortcuts | Common actions (Ctrl+S, etc.) |
| Focus indicators | Visible focus states |

### Mouse/Trackpad Support

| Requirement | Implementation |
|-------------|----------------|
| Hover states | Visual feedback on hover |
| Right-click | Context menu support |
| Scroll | Smooth scrolling |
| Pointer cursor | Appropriate cursor types |

### Stylus Support

| Feature | Implementation |
|---------|----------------|
| Pressure sensitivity | Variable stroke width |
| Palm rejection | Ignore palm touches |
| Tilt detection | Shading effects |
| Hover preview | Show cursor before touch |

## Navigation Patterns

### By Screen Width

| Width | Primary Nav | Secondary Nav |
|-------|-------------|---------------|
| < 600dp | Bottom nav (3-5 items) | Hamburger menu |
| 600-840dp | Navigation rail | Drawer on demand |
| > 840dp | Permanent drawer or rail | Drawer or none |

### Navigation Rail Specs

| Property | Value |
|----------|-------|
| Width | 80dp |
| Icon size | 24dp |
| Touch target | 56dp |
| Items | 3-7 destinations |
| FAB | Optional, at top |

### Permanent Navigation Drawer

| Property | Value |
|----------|-------|
| Width | 256-360dp |
| Position | Left edge (LTR) |
| Behavior | Always visible |
| Content | Full labels, icons |

## Responsive Layouts

### Breakpoints

| Class | Width Range |
|-------|-------------|
| COMPACT | < 600dp |
| MEDIUM | 600-840dp |
| EXPANDED | > 840dp |

Use WindowSizeClass to determine current breakpoint and adapt layout accordingly.

## Content Considerations

### Text Readability

- Line length: 45-75 characters max
- Use multiple columns on wide screens
- Maintain hierarchy with consistent spacing

### Media

- Support multiple aspect ratios
- Provide high-resolution assets
- Consider picture-in-picture for video

### Touch vs. Precise Input

- Large screens often use mouse/keyboard
- Don't assume touch-only interaction
- Provide hover states and tooltips

## Testing

### Device Matrix

| Device Type | Test Priority |
|-------------|---------------|
| Phone (portrait) | Required |
| Phone (landscape) | Required |
| Tablet (both orientations) | Required |
| Foldable (all postures) | High |
| Desktop/Chromebook | Medium |

### Test Cases

- [ ] App fills screen in all configurations
- [ ] No letterboxing or black bars
- [ ] State preserved across configuration changes
- [ ] Multi-window works at minimum size
- [ ] Keyboard navigation functional
- [ ] Mouse hover states present
- [ ] Foldable postures handled (if applicable)
- [ ] Navigation adapts to screen width
