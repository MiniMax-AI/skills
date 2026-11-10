# Image Generation Guide

## CLI usage

```bash
# Basic (default 4K)
python scripts/minimax_image.py "A cat astronaut floating in space" -o cat.png

# 16:9 at 1K
python scripts/minimax_image.py "Mountain landscape at golden hour" -o hero.png --ratio 16:9 --area 1K

# Exact size
python scripts/minimax_image.py "Product photo" -o product.png --size 1024x1024

# Batch: 4 images at once
python scripts/minimax_image.py "Minimalist product icon" -o icons.png -n 4 --ratio 1:1 --area 1K

# Edit with reference images
python scripts/minimax_image.py "Put the hat from Picture 2 on the person in Picture 1" -o out.png --image person.jpg --image hat.png

# Base64 mode (no URL download, save directly)
python scripts/minimax_image.py "Logo concept" -o logo.png --base64 --ratio 1:1 --area 1K
```

## Programmatic usage

```python
from minimax_image import generate_image, download_and_save

# Generate and get URL
result = generate_image("A cat in space", aspect_ratio="16:9", area="1K")
url = result["data"][0]["url"]
download_and_save(url, "cat.png")

# Generate multiple
result = generate_image("Icon design", n=4, aspect_ratio="1:1", area="1K")
for i, item in enumerate(result["data"]):
    download_and_save(item["url"], f"icon-{i}.png")

# Edit with reference images
result = generate_image(
    "Put the hat from Picture 2 on the person in Picture 1",
    images=["person.jpg", "hat.png"],
    aspect_ratio="1:1",
    area="1K",
)
```

## Model

`MiniMax-H3-Image`. Text-to-image uses `/v1/images/generations`. Reference images (`--image`, 1–16) use `/v1/images/edits`.

## Sizing

Use `--ratio` plus `--area` (`1K` / `2K` / `4K`, default `4K`), or `--size WxH` (not together). Area must be at least 655,360 px; aspect ratio between 1:3 and 3:1.

Common ratios: `1:1`, `16:9`, `4:3`, `3:2`, `2:3`, `3:4`, `9:16`, `21:9`.

## Limits

- Batch: 1–10 images per request
- URL expires after 24 hours (use `--base64` to avoid expiry)
- Requests are not idempotent — do not retry a slow call
