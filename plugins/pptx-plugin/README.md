# PPTX Plugin

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python -m markitdown presentation.pptx` |
| Edit or create from template | Read `ppt-editing-skill` |
| Create from scratch | Use subagents + PptxGenJS, see below |

---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx
```

---

## Editing Workflow

**Read `ppt-editing-skill` for full details.**

1. Analyze template with `markitdown`
2. Unpack → manipulate slides → edit content → clean → pack

---

## Creating from Scratch

**Use when no template or reference presentation is available.**

1. Search to understand user requirements
2. Use color-font-skill to select palette and fonts
3. Read ppt-orchestra-skill to design your PPT outline
4. Spawn subagents to create slide JS files (max 5 concurrent)
5. Compile all slide modules into final PPTX

### Subagent Types

- `cover-page-generator` - Cover slide
- `table-of-contents-generator` - TOC slide
- `section-divider-generator` - Section transition
- `content-page-generator` - Content slides
- `summary-page-generator` - Summary/CTA slide

### Output Structure

```
slides/
├── slide-01.js          # Slide modules
├── slide-02.js
├── ...
├── imgs/                # Images used in slides
└── output/              # Final artifacts
    └── presentation.pptx
```

### Tell Subagents

1. File naming: `slides/slide-01.js`, `slides/slide-02.js`
2. Images go in: `slides/imgs/`
3. Final PPTX goes in: `slides/output/`
4. Dimensions: 10" × 5.625" (LAYOUT_16x9)
5. Fonts: Chinese=Microsoft YaHei, English=Arial
6. Colors: 6-char hex without # (e.g. `"FF0000"`)

---

## QA & Dependencies

See **ppt-orchestra-skill** for QA process and dependencies.
