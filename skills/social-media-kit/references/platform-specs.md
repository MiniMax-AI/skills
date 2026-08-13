# Social Media Platform Specs

Image dimensions and aspect ratios for major social media platforms.

## Platform Reference

| Platform | Format | Recommended Size | Aspect Ratio | MiniMax Ratio | Notes |
|----------|--------|-----------------|--------------|---------------|-------|
| Instagram Post | Square | 1080 x 1080 | 1:1 | `1:1` | Feed post, most common format |
| Instagram Story | Vertical | 1080 x 1920 | 9:16 | `9:16` | Full-screen mobile |
| Instagram Reel Cover | Vertical | 1080 x 1920 | 9:16 | `9:16` | Same as Story |
| X/Twitter Post | Landscape | 1200 x 675 | 16:9 | `16:9` | In-feed image |
| X/Twitter Header | Wide | 1500 x 500 | 3:1 | `21:9` | Profile banner (closest match) |
| YouTube Thumbnail | Landscape | 1280 x 720 | 16:9 | `16:9` | Video thumbnail |
| LinkedIn Post | Landscape | 1200 x 627 | ~16:9 | `16:9` | In-feed image |
| LinkedIn Banner | Wide | 1584 x 396 | 4:1 | `21:9` | Profile banner (closest match) |
| Facebook Post | Landscape | 1200 x 630 | ~16:9 | `16:9` | In-feed image |

## MiniMax Supported Aspect Ratios

The MiniMax Image API (`image-01`) supports these aspect ratios:

- `1:1` — Square (Instagram Post)
- `16:9` — Landscape (X, YouTube, LinkedIn, Facebook)
- `4:3` — Classic landscape
- `3:2` — Photo landscape
- `2:3` — Portrait
- `3:4` — Classic portrait
- `9:16` — Vertical (Instagram Story, Reels, TikTok)
- `21:9` — Ultra-wide (banners, headers)

## Composition Tips

### Square (1:1)
- Center the subject
- Keep important elements away from edges
- Works for both product shots and lifestyle images

### Landscape (16:9)
- Use the rule of thirds horizontally
- Leave space for text overlays on one side
- YouTube thumbnails: make text large, use high contrast

### Vertical (9:16)
- Stack elements vertically
- Keep the focal point in the upper 2/3 (bottom may be cut by UI elements)
- Use the full height for impact
