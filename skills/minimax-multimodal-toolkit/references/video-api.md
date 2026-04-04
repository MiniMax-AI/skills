# MiniMax Video Generation API Documentation

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/video_generation` | POST | Create video generation task (all 4 modes) |
| `/v1/query/video_generation` | GET | Query task status |
| `/v1/files/retrieve` | GET | Get video download URL |
| `/v1/video_template_generation` | POST | Create template-based video task |
| `/v1/query/video_template_generation` | GET | Query template task status |

**Base URL:** `https://api.minimaxi.com`
**Auth:** `Authorization: Bearer {MINIMAX_API_KEY}`

---

## Video Generation Models

### Text-to-Video (T2V) Models
| Model | Resolution | Duration | Notes |
|-------|-----------|----------|-------|
| MiniMax-Hailuo-2.3 | 768P (default), 1080P | 6s (1080P), 6/10s (768P) | Recommended, latest |
| MiniMax-Hailuo-2.3-Fast | 768P (default), 1080P | 6s (1080P), 6/10s (768P) | Fast variant |
| MiniMax-Hailuo-02 | 512P, 768P (default), 1080P | 6s (1080P), 6/10s (512P/768P) | Previous gen |
| T2V-01-Director | 720P | 6s | Director control |
| T2V-01 | 720P | 6s | Base model |

### Image-to-Video (I2V) Models
| Model | Resolution | Duration | Notes |
|-------|-----------|----------|-------|
| MiniMax-Hailuo-2.3 | 768P, 1080P | 6s | Recommended |
| MiniMax-Hailuo-2.3-Fast | 768P, 1080P | 6s | Fast variant |
| MiniMax-Hailuo-02 | 512P, 768P, 1080P | 6/10s | Previous gen |
| I2V-01-Director | 720P | 6s | Director control |
| I2V-01-live | 720P | 6s | Live photo style |
| I2V-01 | 720P | 6s | Base model |

### Start-End Frame Model
| Model | Notes |
|-------|-------|
| MiniMax-Hailuo-02 | Only model supporting start-end frame |

### Subject Reference Model
| Model | Notes |
|-------|-------|
| S2V-01 | Face consistency across video |

---

## Request Parameters

### Common Parameters (All Modes)
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| model | string | Yes | - | Model name |
| prompt | string | Depends | - | Video description, max 2000 chars |
| duration | int | No | 6 | Video length in seconds |
| resolution | string | No | 768P/720P | Video resolution |
| prompt_optimizer | bool | No | true | Auto-optimize prompt |
| fast_pretreatment | bool | No | false | Shorten optimizer duration |
| callback_url | string | No | - | Webhook URL |
| aigc_watermark | bool | No | false | Add watermark |

### Image-to-Video Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| first_frame_image | string | Yes | Starting frame (URL or base64 data URL) |

**Image requirements:** JPG/JPEG/PNG/WebP, < 20MB, short side > 300px, aspect ratio 2:5–5:2.

### Start-End Frame Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| first_frame_image | string | Yes | Starting frame |
| last_frame_image | string | Yes | Ending frame |

### Subject Reference Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| subject_reference | array | Yes | Array of subject objects |

Each object has `type` and `image` (array of image URLs):
```json
[{ "type": "character", "image": ["<image_url>"] }]
```

---

## Camera Instructions

Supported in `[指令]` syntax for Hailuo-2.3, Hailuo-02, and Director models:

| Category | Instructions |
|----------|-------------|
| Pan | `[左移]`, `[右移]` |
| Rotation | `[左摇]`, `[右摇]` |
| Push/Pull | `[推进]`, `[拉远]` |
| Elevation | `[上升]`, `[下降]` |
| Tilt | `[上摇]`, `[下摇]` |
| Zoom | `[变焦推近]`, `[变焦拉远]` |
| Other | `[晃动]`, `[跟随]`, `[固定]` |

Combine for simultaneous: `[左摇,上升]` (max 3). Sequential: `...[推进], then ...[拉远]`

---

## Response

**Query status:** `Preparing`, `Queueing`, `Processing`, `Success`, `Fail`

**Error codes:** 0 (success), 1002 (rate limited), 1004 (auth failed), 1008 (insufficient balance), 1026 (sensitive content), 2013 (invalid params), 2049 (invalid API key)

---

## Video Templates

| Template | ID | Input | Description |
|----------|-----|-------|-------------|
| Diving | 392753057216684038 | Image | Diving motion |
| Rings | 393881433990066176 | Image | Gymnastics rings |
| Survival | 393769180141805569 | Image + Text | Outdoor survival |
| Labubu | 394246956137422856 | Image | Labubu character |
| McDonald's Delivery | 393879757702918151 | Image | Pet courier |
| Tibetan Portrait | 393766210733957121 | Image | Cultural portrait |
| Female Model Ads | 393866076583718914 | Image | Female fashion |
| Male Model Ads | 393876118804459526 | Image | Male fashion |
| Winter Romance | 393857704283172856 | Image | Snowy portrait |
| Four Seasons | 398574688191234048 | Image | Seasonal portrait |
| Helpless Moments | 394125185182695432 | Text only | Comedic animation |
