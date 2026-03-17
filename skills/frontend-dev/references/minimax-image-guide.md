# Image Generation Guide

## CLI usage

```bash
# Basic (1:1, 1024x1024)
python scripts/minimax_image.py "A cat astronaut floating in space" -o cat.png

# 16:9 for hero banner
python scripts/minimax_image.py "Mountain landscape at golden hour" -o hero.png --ratio 16:9

# Batch: 4 images at once
python scripts/minimax_image.py "Minimalist product icon" -o icons.png -n 4

# With seed for reproducibility
python scripts/minimax_image.py "Abstract gradient background" -o bg.png --seed 42

# Enable prompt optimization
python scripts/minimax_image.py "a dog" -o dog.png --optimize

# Base64 mode (no URL download, save directly)
python scripts/minimax_image.py "Logo concept" -o logo.png --base64
```

## Programmatic usage

```python
from minimax_image import generate_image, download_and_save

# Generate and get URL
result = generate_image("A cat in space", aspect_ratio="16:9")
url = result["data"]["image_urls"][0]
download_and_save(url, "cat.png")

# Generate multiple
result = generate_image("Icon design", n=4, aspect_ratio="1:1")
for i, url in enumerate(result["data"]["image_urls"]):
    download_and_save(url, f"icon-{i}.png")
```

## Model

Currently only `image-01`.

## Aspect ratios & dimensions

| Ratio | Pixels | Use case |
|-------|--------|----------|
| `1:1` | 1024x1024 | Avatar, icon, square thumbnail |
| `16:9` | 1280x720 | Hero banner, video thumbnail |
| `4:3` | 1152x864 | Standard landscape |
| `3:2` | 1248x832 | Photo-style |
| `2:3` | 832x1248 | Portrait, mobile |
| `3:4` | 864x1152 | Portrait card |
| `9:16` | 720x1280 | Mobile fullscreen, story |
| `21:9` | 1344x576 | Ultra-wide banner |

Custom dimensions also supported: width/height in [512, 2048], must be divisible by 8.

## Limits

- Prompt: max 1,500 characters
- Batch: 1–9 images per request
- URL expires after 24 hours (use `--base64` to avoid expiry)
- Seed: set for reproducible results across identical prompts
