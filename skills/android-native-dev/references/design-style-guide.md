# Design Style Guide

Match visual design to app category and target audience for cohesive user experience.

## Style Selection Principle

> **The visual style must match the app's purpose and audience.**
> A finance app should feel trustworthy, not playful.
> A children's app should feel fun, not corporate.

## Style Selection Matrix

| App Category | Visual Style | Color Palette | Typography | Interaction |
|--------------|--------------|---------------|------------|-------------|
| Utility/Tool | Minimalist | Neutral + 1 accent | Clean sans-serif | Direct, efficient |
| Finance/Banking | Professional Trust | Blue/Green/Navy | Conservative | Secure, deliberate |
| Health/Wellness | Calm & Natural | Soft greens, earth tones | Rounded, friendly | Gentle, encouraging |
| Kids (3-5) | Playful Simple | Bright primary colors | Large, rounded | Big targets, forgiving |
| Kids (6-12) | Fun & Engaging | Vibrant, varied | Bold, readable | Gamified feedback |
| Social/Entertainment | Expressive | Brand-driven | Dynamic | Gesture-rich |
| Productivity | Clean & Focused | Minimal, high contrast | Professional | Keyboard-friendly |
| E-commerce | Conversion-focused | Brand + CTA colors | Scannable | Quick actions |
| Gaming | Immersive | Theme-driven | Stylized | Custom gestures |

## Detailed Style Profiles

### Minimalist / iOS-like (Utility Apps)

**When to use**: Tools, utilities, calculators, file managers, settings apps

**Visual Characteristics**:

| Element | Specification |
|---------|---------------|
| Colors | 2-3 colors max, neutral base |
| Whitespace | Generous, 24-48dp margins |
| Typography | Single font family, clear hierarchy |
| Icons | Line-based, consistent stroke |
| Shadows | Subtle or none |
| Borders | Thin (1dp) or none |
| Shapes | Subtle corners (8-12dp) |

**Interaction Style**:
- Direct manipulation
- Immediate feedback
- No unnecessary animations
- Efficient task completion

**Color Palette**:

| Role | Light Mode | Dark Mode |
|------|------------|-----------|
| Background | #FAFAFA | #1C1C1E |
| Surface | #FFFFFF | #2C2C2E |
| Primary | #007AFF | #0A84FF |
| Text | #000000 | #FFFFFF |
| Secondary | #8E8E93 | #8E8E93 |

**Reference Apps**: iOS Settings, Apple Notes, Google Calculator

---

### Professional Trust (Finance/Business)

**When to use**: Banking, investment, enterprise, B2B applications

**Visual Characteristics**:

| Element | Specification |
|---------|---------------|
| Colors | Blues, greens, navy (trust colors) |
| Whitespace | Structured, grid-based |
| Typography | Formal, conservative weights |
| Icons | Filled or outlined, consistent |
| Data visualization | Clear, accurate charts |
| Security indicators | Prominent locks, badges |

**Interaction Style**:
- Confirmatory (double-check important actions)
- Deliberate (not rushed)
- Secure-feeling
- Clear feedback on transactions

**Color Palette**:

| Role | Color | Name |
|------|-------|------|
| Primary | #00695C or #1565C0 | Teal 800 / Blue 800 |
| Secondary | #37474F | Blue Grey 800 |
| Accent | #FFC107 | Amber |
| Background | #ECEFF1 | Blue Grey 50 |
| Success | #2E7D32 | Green 800 |
| Error | #C62828 | Red 800 |

**Key Patterns**:
- Balance summaries prominent
- Transaction history easily scannable
- Secure entry for sensitive data
- Biometric authentication prompts

**Reference Apps**: Banking apps, Trading platforms, Enterprise tools

---

### Calm & Wellness (Health Apps)

**When to use**: Meditation, fitness tracking, health monitoring, therapy

**Visual Characteristics**:

| Element | Specification |
|---------|---------------|
| Colors | Soft, muted, natural |
| Whitespace | Abundant (breathing room) |
| Typography | Rounded, friendly fonts |
| Shapes | Organic, soft corners (16dp+) |
| Animation | Gentle, slow transitions |
| Imagery | Nature, soft gradients |

**Interaction Style**:
- Encouraging, not demanding
- Progress-oriented
- Gentle reminders
- Celebration of achievements

**Color Palette**:

| Role | Color | Name |
|------|-------|------|
| Primary | #4CAF50 | Green 500 |
| Secondary | #81C784 | Green 300 |
| Tertiary | #B2DFDB | Teal 100 |
| Background | #F1F8E9 | Light Green 50 |
| Text | #33691E | Light Green 900 |
| Accent | #FFB74D | Orange 300 |

**Key Patterns**:
- Progress rings and charts
- Streak tracking
- Motivational messages
- Quiet notification style

**Reference Apps**: Headspace, Calm, Apple Fitness

---

### Playful & Kid-Friendly (Children's Apps)

**When to use**: Educational games, children's content, family apps

#### Ages 3-5

**Visual Characteristics**:

| Element | Specification |
|---------|---------------|
| Colors | Bright, saturated primary colors |
| Touch targets | 56dp minimum, 64dp recommended |
| Shapes | Very rounded (full radius) |
| Typography | Large (18sp+ minimum), simple fonts |
| Icons | Large, colorful, recognizable |
| Animation | Frequent, rewarding |

**Interaction Style**:
- Simple gestures only (tap, drag)
- No multi-finger gestures
- Forgiving error handling
- Immediate, multi-sensory feedback (sound + visual + haptic)
- No text-only buttons

**Color Palette**:

| Role | Color | Name |
|------|-------|------|
| Primary | #F44336 | Red 500 |
| Secondary | #FFEB3B | Yellow 500 |
| Tertiary | #2196F3 | Blue 500 |
| Background | #FFFFFF | White or soft pastels |
| Accent | #4CAF50 | Green 500 |

#### Ages 6-12

**Visual Characteristics**:

| Element | Specification |
|---------|---------------|
| Colors | Vibrant, varied palette |
| Touch targets | 48dp minimum |
| Shapes | Rounded but can be varied |
| Typography | Bold, readable, can include text |
| Icons | Stylized, character-driven |
| Animation | Gamified, achievement-based |

**Interaction Style**:
- Can introduce some complexity
- Gamification elements
- Progress and rewards
- Some text is acceptable

**Key Patterns for All Kids Apps**:
- Icon-based navigation (no text-only)
- Home button always visible
- Back navigation clear
- Parent gate for settings (math problem, hold button)
- Multi-sensory feedback
- Encouraging error states (no punishment)
- Joint engagement opportunities with parents

**Reference Apps**: PBS Kids, Khan Academy Kids, Duolingo ABC

---

### Expressive & Social (Entertainment Apps)

**When to use**: Social media, content creation, entertainment

**Visual Characteristics**:

| Element | Specification |
|---------|---------------|
| Colors | Bold brand colors |
| Typography | Dynamic, personality-driven |
| Media | Rich, prominent |
| Animation | Expressive, delightful |
| Shapes | Brand-specific |

**Interaction Style**:
- Gesture-rich
- Quick actions
- Social interactions prominent
- Content-first design

**Key Patterns**:
- Feed-based layouts
- Quick action buttons (like, share, comment)
- Stories/ephemeral content
- Creation tools accessible
- Notification badges

**Reference Apps**: Instagram, TikTok, Snapchat

---

### Clean & Focused (Productivity Apps)

**When to use**: Note-taking, task management, email, documents

**Visual Characteristics**:

| Element | Specification |
|---------|---------------|
| Colors | High contrast, minimal |
| Whitespace | Strategic, content-focused |
| Typography | Highly readable, clear hierarchy |
| Icons | Functional, consistent |
| Density | Adjustable (compact to comfortable) |

**Interaction Style**:
- Keyboard-friendly
- Batch operations
- Drag and drop
- Quick capture
- Search-centric

**Color Palette**:

| Role | Light Mode | Dark Mode |
|------|------------|-----------|
| Primary | #1976D2 | #64B5F6 |
| Background | #FFFFFF | #121212 |
| Surface | #F5F5F5 | #1E1E1E |
| Text | #212121 | #E0E0E0 |
| Accent/Priority | #FF5722 | #FF7043 |

**Key Patterns**:
- List views with swipe actions
- Quick add buttons
- Checkbox interactions
- Due dates and reminders
- Tags and categories

**Reference Apps**: Notion, Todoist, Google Tasks

---

### Conversion-Focused (E-commerce)

**When to use**: Shopping, marketplace, booking apps

**Visual Characteristics**:

| Element | Specification |
|---------|---------------|
| Colors | Brand + clear CTA colors |
| Images | High quality, zoomable |
| Typography | Scannable, price prominent |
| Cards | Product-focused |
| Badges | Sale, new, limited |

**Interaction Style**:
- Quick add to cart
- Easy checkout flow
- Comparison features
- Reviews accessible
- Wishlist/save for later

**Key Patterns**:
- Grid and list view toggle
- Filter and sort
- Product detail with gallery
- Cart always accessible
- One-tap purchase options

**Reference Apps**: Amazon, Shopify apps, Booking.com

---

## Consistency Principles

### Match Style to Subject Matter

| App Purpose | Style Should Feel |
|-------------|-------------------|
| Utility | Efficient, invisible |
| Finance | Trustworthy, secure |
| Health | Supportive, calm |
| Kids | Safe, fun |
| Social | Expressive, personal |
| Productivity | Focused, powerful |
| Shopping | Exciting, trustworthy |

### Internal Consistency Rules

| Rule | Implementation |
|------|----------------|
| Same icon style | All outlined OR all filled |
| Consistent color meaning | Red = destructive, Green = success |
| Uniform spacing | Use 8dp grid |
| Predictable interaction | Same gesture = same result |
| Typography system | Use M3 type scale |

## Anti-Patterns: Style Mismatch

| Mismatch | Problem |
|----------|---------|
| Playful colors in banking app | Undermines trust |
| Complex gestures in kids app | Frustrates young users |
| Cluttered UI in wellness app | Defeats calming purpose |
| Boring visuals in entertainment | Fails to engage |
| Aggressive CTAs in health app | Feels manipulative |
| Childish design in professional tool | Lacks credibility |
| Dense information in casual app | Overwhelms users |

## Implementation Checklist

- [ ] Identified app category and target audience
- [ ] Selected appropriate style profile
- [ ] Color palette matches style
- [ ] Typography matches style
- [ ] Interaction patterns match style
- [ ] Touch targets appropriate for audience
- [ ] Animation style consistent
- [ ] Internal consistency maintained
- [ ] No style mismatches
- [ ] Tested with target users
