# MiniMax Music Generation API (music-2.5)

Source: https://platform.minimaxi.com/docs/api-reference/music-generation

## Endpoint

`POST https://api.minimaxi.com/v1/music_generation`

## Auth

`Authorization: Bearer <MINIMAX_API_KEY>`

## Request (JSON)

Required:
- `model`: string — `music-2.5`
- `lyrics`: string (1–3500 chars) — required. Use `\n` for line breaks. Structure tags: `[Verse]`, `[Chorus]`, `[Bridge]`, `[Intro]`, `[Outro]`, etc.

Optional:
- `prompt`: string (0–2000 chars) — style description, optional but recommended.
- `lyrics_optimizer`: boolean — auto-generate lyrics from prompt when lyrics is empty.
- `stream`: boolean (default `false`)
- `output_format`: `hex` (default) or `url`. URL valid for 24 hours.
- `aigc_watermark`: boolean — top-level field, non-streaming only.
- `audio_setting`:
  - `sample_rate`: 16000, 24000, 32000, 44100
  - `bitrate`: 32000, 64000, 128000, 256000
  - `format`: mp3, wav, pcm

## Example

```json
{
  "model": "music-2.5",
  "prompt": "indie folk, melancholic, introspective",
  "lyrics": "[verse]\n...\n[chorus]\n...",
  "aigc_watermark": false,
  "audio_setting": {
    "sample_rate": 44100,
    "bitrate": 256000,
    "format": "mp3"
  }
}
```

## Response

- `data.audio`: hex string or URL depending on `output_format`
- `data.status`: 1 (generating), 2 (complete)
- `extra_info`: duration, sample_rate, channels, bitrate, size
- `base_resp.status_code`: 0 on success

## Notes

- `music-2.5` does not support `is_instrumental`. For instrumental music, use lyrics `[intro] [outro]` and add `pure music, no lyrics` to the prompt.
- `prompt` is optional but recommended for better style control.
- `stream=true` only supports `hex` output.
