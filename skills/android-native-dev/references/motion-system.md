# Motion System Guidelines

Animation and transition specifications for Material Design 3.

## Motion Principles

### Four Core Characteristics

| Principle | Description |
|-----------|-------------|
| **Responsive** | Quickly responds to user input at the point of interaction |
| **Natural** | Follows real-world physics (gravity, friction, momentum) |
| **Aware** | Elements are aware of surroundings and other elements |
| **Intentional** | Guides focus to the right place at the right time |

## Duration Guidelines

### By Interaction Type

| Type | Duration | Usage |
|------|----------|-------|
| Micro | 50-100ms | Ripples, state changes, hover |
| Short | 100-200ms | Simple transitions, toggles |
| Medium | 200-300ms | Expanding, collapsing, revealing |
| Long | 300-500ms | Complex choreography, page transitions |

### By Device Type

| Device | Typical Duration | Adjustment |
|--------|------------------|------------|
| Mobile | 300ms | Baseline |
| Tablet | 390ms | +30% slower |
| Desktop | 150-200ms | Faster, more responsive |
| Wearable | 210ms | -30% faster |

### Duration Rules

- **Maximum**: Keep under 400ms for most transitions
- **User-initiated**: Faster (closer to instant feedback)
- **System-initiated**: Can be slightly longer
- **Loading states**: Use indeterminate indicators for unknown duration

## Easing Curves

### Standard Curves

| Curve | Usage | Characteristics |
|-------|-------|-----------------|
| **Standard** | Most common transitions | Quick acceleration, slow deceleration |
| **Emphasized** | Important/significant transitions | More dramatic curve |
| **Decelerate** | Elements entering screen | Starts fast, ends slow |
| **Accelerate** | Elements leaving screen permanently | Starts slow, ends fast |
| **Sharp** | Elements temporarily leaving | Quick, snappy motion |

### Curve Values (Cubic Bezier)

| Curve | Value |
|-------|-------|
| Standard | cubic-bezier(0.2, 0.0, 0.0, 1.0) |
| Emphasized | cubic-bezier(0.2, 0.0, 0.0, 1.0) |
| Decelerate | cubic-bezier(0.0, 0.0, 0.0, 1.0) |
| Accelerate | cubic-bezier(0.3, 0.0, 1.0, 1.0) |

## Movement Patterns

### Arc Motion

- Use natural, concave arcs for diagonal movement
- Single-axis movement (horizontal/vertical only) stays straight
- Elements entering/exiting screen move on single axis

### Choreography

- **Stagger**: Offset timing for related elements (20-40ms between)
- **Cascade**: Sequential reveal from a focal point
- **Shared motion**: Elements that move together maintain relationship

## Transition Patterns

### Container Transform

Best for: Navigation from card/list item to detail screen

- Origin container morphs into destination
- Maintains visual continuity
- Content fades during transformation

### Shared Axis

Best for: Same-level navigation (tabs, stepper)

| Axis | Direction | Usage |
|------|-----------|-------|
| X-axis | Horizontal | Tabs, horizontal paging |
| Y-axis | Vertical | Vertical lists, feeds |
| Z-axis | Depth | Parent-child relationships |

### Fade Through

Best for: Unrelated screen transitions

- Outgoing content fades out
- Incoming content fades in
- Brief overlap period
- No shared elements

### Fade

Best for: Show/hide single elements

- Simple opacity change
- Optionally combine with scale
- Quick duration (100-200ms)

## Component-Specific Motion

### FAB

| State | Animation |
|-------|-----------|
| Appear | Scale up + fade in |
| Disappear | Scale down + fade out |
| Transform | Morph to extended FAB |
| Press | Elevation change (3dp → 8dp) |

### Bottom Sheet

| State | Animation |
|-------|-----------|
| Expand | Slide up with decelerate curve |
| Collapse | Slide down with accelerate curve |
| Dismiss | Swipe down with velocity-based duration |

### Navigation

| Pattern | Animation |
|---------|-----------|
| Push | Incoming slides from right, outgoing shifts left |
| Pop | Incoming slides from left, outgoing shifts right |
| Modal | Slide up from bottom |

### Cards

| State | Animation |
|-------|-----------|
| Expand | Container transform to detail |
| Press | Subtle elevation increase |
| Reorder | Follow finger with physics |

## Loading & Progress

### Indeterminate Indicators

- Use for unknown duration
- Continuous, looping animation
- M3 Expressive: Customizable waveform and thickness

### Determinate Indicators

- Use when progress is measurable
- Smooth, linear progression
- Update frequently for responsiveness

### Skeleton Screens

- Show layout structure immediately
- Subtle shimmer animation
- Replace with content as it loads

## Accessibility Considerations

### Reduced Motion

- Respect prefers-reduced-motion setting
- Provide alternatives:
  - Instant transitions (no animation)
  - Simple fade instead of complex motion
  - Static loading indicators

### Motion Duration

- Keep essential feedback < 100ms
- Avoid motion that could trigger vestibular issues
- Test with motion sensitivity settings enabled

## Implementation Notes

### Android Animation APIs

| API | Usage |
|-----|-------|
| MotionLayout | Complex, coordinated animations |
| Transition | Activity/Fragment transitions |
| Animator | Property animations |
| AnimatedContent | Compose content transitions |
| animateContentSize | Compose size changes |

### Performance Tips

- Use hardware layers for complex animations
- Avoid animating layout properties (use transform)
- Profile with GPU rendering tools
- Target 60 FPS (16ms per frame)
