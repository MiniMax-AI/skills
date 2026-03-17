# Visual Design Guidelines

Detailed specifications for colors, typography, spacing, elevation, and shapes in Material Design 3.

## Color System

### Color Roles (Tokens)

Material Design 3 uses a token-based color system with three accent groups:

| Role | Usage |
|------|-------|
| **Primary** | Key components, FAB, prominent buttons |
| **Secondary** | Less prominent components, filters, chips |
| **Tertiary** | Accent, complementary elements |
| **Error** | Error states, destructive actions |
| **Surface** | Backgrounds, cards, dialogs |

Each role includes variants: base color, onColor, container, onContainer.

### Color Contrast Requirements

| Element | Minimum Contrast Ratio | Notes |
|---------|----------------------|-------|
| Body text | **4.5:1** | WCAG AA compliance |
| Large text (18sp+) | **3:1** | 14sp bold also qualifies |
| UI components | **3:1** | Icons, borders, controls |
| Focus indicators | **3:1** | Must be clearly visible |

### Recommended Color Palettes

#### Modern Professional (Business Apps)

| Role | Color | Name |
|------|-------|------|
| Primary | #1976D2 | Blue 700 |
| Secondary | #455A64 | Blue Grey 700 |
| Tertiary | #00897B | Teal 600 |
| Background | #FAFAFA | Grey 50 |

#### Vibrant & Playful (Consumer Apps)

| Role | Color | Name |
|------|-------|------|
| Primary | #6200EE | Deep Purple |
| Secondary | #03DAC6 | Teal Accent |
| Tertiary | #FF5722 | Deep Orange |
| Background | #FFFFFF | White |

#### Dark & Elegant (Premium Apps)

| Role | Color | Name |
|------|-------|------|
| Primary | #BB86FC | Purple 200 |
| Secondary | #03DAC6 | Teal 200 |
| Tertiary | #CF6679 | Red 200 |
| Background | #121212 | Dark surface |

#### Nature & Wellness (Health Apps)

| Role | Color | Name |
|------|-------|------|
| Primary | #4CAF50 | Green 500 |
| Secondary | #8BC34A | Light Green 500 |
| Tertiary | #FFEB3B | Yellow 500 |
| Background | #F1F8E9 | Light Green 50 |

#### Finance & Trust (Banking Apps)

| Role | Color | Name |
|------|-------|------|
| Primary | #00695C | Teal 800 |
| Secondary | #37474F | Blue Grey 800 |
| Tertiary | #FFC107 | Amber 500 |
| Background | #ECEFF1 | Blue Grey 50 |

### Dark Theme Requirements

- Background: #121212 or darker
- Surface colors use elevation-based tonal overlay
- Primary colors should be lighter variants (200-300 range)
- Maintain contrast ratios in dark mode
- Test all states (hover, focus, pressed) in dark mode

## Typography System

### Type Scale

| Style | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| Display Large | 57sp | 400 | 64sp | Hero text |
| Display Medium | 45sp | 400 | 52sp | Large headers |
| Display Small | 36sp | 400 | 44sp | Section headers |
| Headline Large | 32sp | 400 | 40sp | Screen titles |
| Headline Medium | 28sp | 400 | 36sp | Subsection titles |
| Headline Small | 24sp | 400 | 32sp | Card titles |
| Title Large | 22sp | 400 | 28sp | App bar titles |
| Title Medium | 16sp | 500 | 24sp | List item titles |
| Title Small | 14sp | 500 | 20sp | Tabs |
| Body Large | 16sp | 400 | 24sp | Primary body text |
| Body Medium | 14sp | 400 | 20sp | Secondary body text |
| Body Small | 12sp | 400 | 16sp | Captions |
| Label Large | 14sp | 500 | 20sp | Button text |
| Label Medium | 12sp | 500 | 16sp | Navigation labels |
| Label Small | 11sp | 500 | 16sp | Badges |

### Recommended Fonts

| Category | Fonts |
|----------|-------|
| Primary | Roboto (system default) |
| Display | Roboto Serif, Google Sans |
| Monospace | Roboto Mono, JetBrains Mono |

### Text Readability

- **Line length**: 45-75 characters per line (including spaces)
- **Paragraph spacing**: 1.5x line height between paragraphs
- **Letter spacing**: Use default unless brand requires adjustment
- **Text alignment**: Left-aligned for body text (LTR languages)

## Spacing & Layout

### 8dp Grid System

All spacing values should be multiples of 8dp (with 4dp for fine adjustments).

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4dp | Icon padding, fine adjustments |
| sm | 8dp | Tight spacing, inline elements |
| md | 16dp | Default padding, card content |
| lg | 24dp | Section spacing |
| xl | 32dp | Large gaps, group separation |
| xxl | 48dp | Screen margins, major sections |

### Component Dimensions

| Component | Height | Min Width | Notes |
|-----------|--------|-----------|-------|
| Button | 40dp | 64dp | Touch target 48dp |
| FAB | 56dp | 56dp | Standard size |
| Mini FAB | 40dp | 40dp | Secondary actions |
| Extended FAB | 56dp | 80dp | With text label |
| Text Field | 56dp | 280dp | Including label |
| App Bar | 64dp | - | Top app bar |
| Bottom Nav | 80dp | - | With labels |
| Nav Rail | - | 80dp | Tablet/desktop |
| List Item | 56-88dp | - | Depends on content |
| Chip | 32dp | - | Filter/action chips |

### Touch Targets

| Type | Size | Notes |
|------|------|-------|
| Minimum | 48 × 48dp | WCAG requirement |
| Recommended | 56 × 56dp | Primary actions |
| Kids apps | 56dp+ | Larger for motor skills |
| Spacing | 8dp minimum | Between adjacent targets |

## Elevation & Shadows

### Elevation Levels

| Level | Elevation | Usage |
|-------|-----------|-------|
| Level 0 | 0dp | Flat surfaces |
| Level 1 | 1dp | Cards, elevated buttons |
| Level 2 | 3dp | FAB (resting), raised elements |
| Level 3 | 6dp | Navigation drawer, bottom sheet |
| Level 4 | 8dp | FAB (pressed), menus |
| Level 5 | 12dp | Dialogs, modal surfaces |

### Shadow Guidelines

- Use elevation consistently for same component types
- Higher elevation = more important/prominent
- In dark theme, use surface tint instead of shadows
- Avoid excessive elevation (keeps UI grounded)

## Shape System

### Corner Radius

| Size | Radius | Usage |
|------|--------|-------|
| None | 0dp | Sharp edges, dividers |
| Extra Small | 4dp | Badges, small chips |
| Small | 8dp | Buttons, chips, small cards |
| Medium | 12dp | Cards, dialogs, text fields |
| Large | 16dp | FAB, bottom sheets |
| Extra Large | 28dp | Large sheets, expanded cards |
| Full | 50% | Pills, avatars, circular buttons |

### M3 Expressive Shapes

Material 3 Expressive introduces 35 new decorative shapes:
- Organic curves
- Asymmetric corners
- Cut corners
- Scalloped edges

Use sparingly for brand differentiation and visual interest.

### Shape Consistency Rules

- Same component type = same shape
- Related components should share shape family
- Don't mix too many shape styles on one screen
- Consider shape in dark/light theme transitions

## Icons

### Size Specifications

| Size | Dimensions | Usage |
|------|------------|-------|
| Small | 20 × 20dp | Compact UI, inline |
| Standard | 24 × 24dp | Default for most uses |
| Large | 40 × 40dp | Emphasis, empty states |

### Icon Guidelines

- **Touch target**: Always wrap in 48dp minimum clickable area
- **Style**: Outlined (default), Filled (selected/active states)
- **Stroke width**: 2dp for outlined icons
- **Optical alignment**: May need visual adjustments
- **Color**: Use semantic colors (primary, error, etc.)

### Recommended Icon Sets

| Set | Usage |
|-----|-------|
| Material Symbols | Recommended, variable font support |
| Material Icons | Legacy, still widely used |

### Adaptive Icons (App Icon)

| Property | Value |
|----------|-------|
| Canvas size | 108 × 108dp |
| Safe zone | 66 × 66dp (centered circle) |
| Logo size | 48-66dp |
| Max display | 72 × 72dp |
| Layers | Foreground + Background (both 108dp) |
| Android 13+ | Include monochrome layer for theming |
