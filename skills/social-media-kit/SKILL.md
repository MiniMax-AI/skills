---
name: social-media-kit
description: |
  Generate branded social media content packs using MiniMax Image API.
  Use when: creating social media posts, generating branded images for multiple platforms,
  batch content creation for Instagram, X/Twitter, YouTube, LinkedIn.
  Triggers: social media, content pack, Instagram post, YouTube thumbnail, branded images,
  marketing visuals, social content, platform images.
license: MIT
metadata:
  version: "1.0"
  category: creative-tools
  output_format: png
  sources:
    - MiniMax Image Generation API (image-01)
---

# Social Media Kit

Generate branded image packs for social media platforms.

## Prerequisites

Before starting, ensure:

1. **Python venv** is activated with dependencies from [requirements.txt](references/requirements.txt) installed
2. **`MINIMAX_API_KEY`** is exported (e.g. `export MINIMAX_API_KEY='your-key'`)

If any prerequisite is missing, set it up first. Do NOT proceed without both.

## Workflow

### Step 0: Brand Brief

Collect brand information from the user:

> "Tell me about your brand or product. I need: name, visual style (colors, mood), and what the content is about."

Extract:
- **Brand name** - used in file naming
- **Visual style** - colors, mood, aesthetic direction
- **Content theme** - what the images should communicate
- **Target audience** - informs composition and style

### Step 1: Platform Selection

Present the available platforms. Reference [platform-specs.md](references/platform-specs.md) for dimensions.

| Platform | Format | Aspect Ratio |
|----------|--------|--------------|
| Instagram Post | Square | 1:1 |
| Instagram Story | Vertical | 9:16 |
| X/Twitter Post | Landscape | 16:9 |
| YouTube Thumbnail | Landscape | 16:9 |
| LinkedIn Post | Landscape | 16:9 |

Ask the user:
> "Which platforms do you need images for? Pick all that apply, or say 'all' for the full set."

### Step 2: Prompt Engineering

For each selected platform, craft an image generation prompt that accounts for:

1. **Composition** - square images need centered subjects, wide images need horizontal layouts, tall images need vertical stacking
2. **Brand elements** - incorporate the brand colors and style
3. **Text-safe zones** - leave space for overlay text on thumbnails and posts
4. **Platform conventions** - YouTube thumbnails are bold and high-contrast, Instagram posts are polished and aspirational, LinkedIn is professional

**Prompt template per platform:**

- **Instagram Post (1:1):** `"{content theme}, centered composition, {visual style}, clean and polished, social media post, square format"`
- **Instagram Story (9:16):** `"{content theme}, vertical composition, {visual style}, full-height layout, mobile-first design"`
- **X/Twitter Post (16:9):** `"{content theme}, wide horizontal composition, {visual style}, clean background, room for text overlay"`
- **YouTube Thumbnail (16:9):** `"{content theme}, bold and eye-catching, {visual style}, high contrast, dramatic lighting, thumbnail style"`
- **LinkedIn Post (16:9):** `"{content theme}, professional and clean, {visual style}, corporate-friendly, modern business aesthetic"`

### Step 3: Generate Images

**Tool**: `scripts/social_kit.py`

Generate all images in one batch:

```bash
python3 scripts/social_kit.py \
  --brand "Brand Name" \
  --prompt "content theme, visual style" \
  --platforms instagram_post instagram_story x_post youtube_thumb linkedin_post \
  -o output/
```

Or generate individually with `minimax_image.py`:

```bash
python3 scripts/minimax_image.py "prompt for instagram" -o output/brand_instagram_post.png --ratio 1:1
python3 scripts/minimax_image.py "prompt for story" -o output/brand_instagram_story.png --ratio 9:16
python3 scripts/minimax_image.py "prompt for x" -o output/brand_x_post.png --ratio 16:9
python3 scripts/minimax_image.py "prompt for youtube" -o output/brand_youtube_thumb.png --ratio 16:9
python3 scripts/minimax_image.py "prompt for linkedin" -o output/brand_linkedin_post.png --ratio 16:9
```

All calls are independent - **run concurrently** for speed.

### Step 4: Review & Iterate

Show the generated images to the user. For each image:
- If the user approves, keep it
- If they want changes, regenerate with an adjusted prompt
- Offer to generate variations (up to 4 per platform via the `--n` flag)

### Step 5: Deliver

Output format:
1. Summary line with count
2. File listing with platform labels

```
Social media kit created: 5 images for "Brand Name"

  Instagram Post (1:1):    output/brand_instagram_post.png
  Instagram Story (9:16):  output/brand_instagram_story.png
  X/Twitter Post (16:9):   output/brand_x_post.png
  YouTube Thumbnail (16:9): output/brand_youtube_thumb.png
  LinkedIn Post (16:9):    output/brand_linkedin_post.png
```

## Rules

- Always use the correct aspect ratio for each platform. Wrong dimensions look unprofessional.
- All image prompts must be in **English** regardless of user language.
- File names follow the pattern: `{brand}_{platform}.png` (lowercase, underscores).
- Generate at least 1 image per selected platform. Offer variations if the user wants options.
- YouTube thumbnails need bold, high-contrast compositions. They are viewed at small sizes.
- Instagram Stories are viewed on mobile. Keep visual elements large and centered.
