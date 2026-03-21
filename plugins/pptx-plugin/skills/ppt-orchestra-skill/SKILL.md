---
name: ppt-orchestra-skill
description: "Plan and orchestrate multi-slide PowerPoint creation from scratch. Use before generating a full deck with subagents: classify each slide type, enforce visual variety, set typography/spacing rules, and run text-based QA to catch content issues."
license: Proprietary. LICENSE.txt has complete terms
---

# Slide Page Types (Standard)

For slide-by-slide generation (one JS file per slide), classify **every slide** as **exactly one** of these 5 page types. This keeps structure consistent and prevents "random layout drift".

1. **Cover Page**
   - **Use for**: opening + tone setting
   - **Content**: big title, subtitle/presenter, date/occasion, strong background/motif
2. **Table of Contents**
   - **Use for**: navigation + expectation setting (3–5 sections)
   - **Content**: section list (optional icons / page numbers)
3. **Section Divider**
   - **Use for**: clear transitions between major parts
   - **Content**: section number + title (+ optional 1–2 line intro)
4. **Content Page** (pick a subtype)
   - **Text**: bullets/quotes/short paragraphs (still add icons/shapes)
   - **Mixed media**: two-column / half-bleed image + text overlay
   - **Data visualization**: chart + 1–3 key takeaways + **source**
   - **Comparison**: side-by-side columns/cards (A vs B, pros/cons)
   - **Timeline / process**: steps with arrows, journey, phases
   - **Image showcase**: hero image, gallery, or visual-first layout
5. **Summary / Closing Page**
   - **Use for**: wrap-up + action
   - **Content**: key takeaways, CTA/next steps, contact/QR, thank-you

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

**Choose an interesting font pairing** — don't default to Arial. Pick a header font with personality and pair it with a clean body font.

| Header Font | Body Font |
|-------------|-----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt muted |

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead

## Compiling Slides

After all slide JS files are generated in `slides/`, create `slides/compile.js` to compile them into a single PPTX:

```javascript
// slides/compile.js
const pptxgen = require('pptxgenjs');
const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';

const theme = {
  primary: "22223b",    // dark color for backgrounds/text
  secondary: "4a4e69",  // secondary accent
  accent: "9a8c98",     // highlight color
  light: "c9ada7",      // light accent
  bg: "f2e9e4"          // background color
};

for (let i = 1; i <= 12; i++) {  // adjust count as needed
  const num = String(i).padStart(2, '0');
  const slideModule = require(`./slide-${num}.js`);
  slideModule.createSlide(pres, theme);
}

pres.writeFile({ fileName: './output/presentation.pptx' });
```

Run with: `cd slides && node compile.js`

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Verification Loop

1. Generate slides → Extract text with `python -m markitdown output.pptx` → Review content
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

---

## Dependencies

- `pip install "markitdown[pptx]"` - text extraction
- `npm install -g pptxgenjs` - creating from scratch
