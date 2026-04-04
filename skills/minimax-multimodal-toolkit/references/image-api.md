# MiniMax Image Generation API (image-01)

Source: https://platform.minimaxi.com/docs/api-reference/image-generation-t2i and https://platform.minimaxi.com/docs/api-reference/image-generation-i2i

## Endpoint

`POST https://api.minimaxi.com/v1/image_generation`

## Auth

`Authorization: Bearer <MINIMAX_API_KEY>`

## Request (JSON)

Required:
- `model`: string — `image-01`
- `prompt`: string (max 1500 chars) — text description of the desired image

Optional:
- `aspect_ratio`: string — image aspect ratio, default `1:1`. Options:
  - `1:1` (1024×1024)
  - `16:9` (1280×720)
  - `4:3` (1152×864)
  - `3:2` (1248×832)
  - `2:3` (832×1248)
  - `3:4` (864×1152)
  - `9:16` (720×1280)
  - `21:9` (1344×576)
- `width`: integer — custom width in pixels. Range [512, 2048], must be multiple of 8. Overridden by `aspect_ratio` if both set.
- `height`: integer — custom height in pixels. Same rules as `width`. Both `width` and `height` must be set together.
- `response_format`: string — `url` (default, valid 24h) or `base64`
- `n`: integer (1–9, default 1) — number of images to generate
- `seed`: integer — random seed for reproducibility
- `prompt_optimizer`: boolean (default `false`) — enable automatic prompt optimization
- `aigc_watermark`: boolean (default `false`) — add AIGC watermark

### Subject Reference (image-to-image)

- `subject_reference`: array — character reference for image-to-image generation
  - `type`: string — currently only `character` (portrait)
  - `image_file`: string — reference image as public URL or Base64 Data URL (`data:image/jpeg;base64,...`). For best results, use a single person front-facing photo. Formats: JPG, JPEG, PNG. Max size: 10MB.

## Example — Text-to-Image

```json
{
  "model": "image-01",
  "prompt": "A man in a white t-shirt, full-body, standing front view, outdoors, with the Venice Beach sign in the background, Los Angeles. Fashion photography in 90s documentary style, film grain, photorealistic.",
  "aspect_ratio": "16:9",
  "response_format": "url",
  "n": 3,
  "prompt_optimizer": true
}
```

## Example — Image-to-Image (Character Reference)

```json
{
  "model": "image-01",
  "prompt": "A girl looking into the distance from a library window",
  "aspect_ratio": "16:9",
  "subject_reference": [
    {
      "type": "character",
      "image_file": "https://example.com/face.jpg"
    }
  ],
  "n": 2
}
```

## Response

```json
{
  "id": "03ff3cd0820949eb8a410056b5f21d38",
  "data": {
    "image_urls": ["https://...", "https://...", "https://..."],
    "image_base64": null
  },
  "metadata": {
    "success_count": 3,
    "failed_count": 0
  },
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```

- `data.image_urls`: array of image URLs (when `response_format` is `url`, valid 24h)
- `data.image_base64`: array of Base64 strings (when `response_format` is `base64`)
- `metadata.success_count`: number of successfully generated images
- `metadata.failed_count`: number of images blocked by content safety

## Status Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1002 | Rate limited, retry later |
| 1004 | Auth failed, check API key |
| 1008 | Insufficient balance |
| 1026 | Prompt contains sensitive content |
| 2013 | Invalid parameters |
| 2049 | Invalid API key |

## Notes

- The API is synchronous — images are returned directly in the response (no polling needed).
- URL format image links expire after 24 hours.
- For image-to-image: upload a single front-facing portrait for best character reference results.
- `width`/`height` are overridden by `aspect_ratio` if both provided.
