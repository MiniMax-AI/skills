---
name: minimax-multimodal-toolkit
description: Use mmx to generate text, images, video, and speech, and to transcribe audio, via the MiniMax AI platform. Use when the user wants to create media content, chat with MiniMax models, transcribe audio to text, perform web search, or manage MiniMax API resources from the terminal.
---

# MiniMax CLI — Agent Skill Guide

Use `mmx` to generate text, images, video, speech, transcribe audio, and perform web search via the MiniMax AI platform.

## Prerequisites

```bash
# Install
npm install -g mmx-cli

# Auth (OAuth persists to ~/.mmx/credentials.json, API key persists to ~/.mmx/config.json)
mmx auth login --api-key sk-xxxxx

# Verify active auth source
mmx auth status

# Or pass per-call
mmx text chat --api-key sk-xxxxx --message "Hello"
```

Region is auto-detected. Override with `--region global` or `--region cn`.

---

## Agent Flags

Always use these flags in non-interactive (agent/CI) contexts:

| Flag | Purpose |
|---|---|
| `--non-interactive` | Fail fast on missing args instead of prompting |
| `--quiet` | Suppress spinners/progress; stdout is pure data |
| `--output json` | Machine-readable JSON output |
| `--async` | Return task ID immediately (video generation) |
| `--dry-run` | Preview the API request without executing |
| `--yes` | Skip confirmation prompts |

---

## Commands

### text chat

Chat completion. Default model: `MiniMax-M3.1-Flash`. An explicit `--model` or saved `default-text-model` takes precedence. This model currently requires M Plan or MiniMax Code; with a pay-as-you-go key, use `--model MiniMax-M3`. Thinking is enabled by default with `max` effort. See the [model guide](https://platform.minimax.io/docs/guides/text-generation#agent).

```bash
mmx text chat --message <text> [flags]
```

| Flag | Type | Description |
|---|---|---|
| `--message <text>` | string, **required**, repeatable | Message text. Prefix with `role:` to set role (e.g. `"system:You are helpful"`, `"user:Hello"`) |
| `--messages-file <path>` | string | JSON file with messages array. Use `-` for stdin |
| `--system <text>` | string | System prompt |
| `--model <model>` | string | Model ID (default: `MiniMax-M3.1-Flash`) |
| `--max-tokens <n>` | number | Max tokens (default: 4096) |
| `--temperature <n>` | number | Sampling temperature (0.0, 1.0] |
| `--top-p <n>` | number | Nucleus sampling threshold |
| `--stream` | boolean | Stream tokens (default: on in TTY) |
| `--tool <json-or-path>` | string, repeatable | Tool definition JSON or file path |

```bash
# Single message
mmx text chat --message "user:What is MiniMax?" --output json --quiet

# Multi-turn
mmx text chat \
  --system "You are a coding assistant." \
  --message "user:Write fizzbuzz in Python" \
  --output json

# From file
cat conversation.json | mmx text chat --messages-file - --output json
```

**stdout**: response text (text mode) or full response object (json mode).

---

### image generate

Generate or edit images with `MiniMax-H3-Image` (up to 20 MP). Always pass `--model MiniMax-H3-Image`. Use `--image` for image editing.

```bash
mmx image generate --model MiniMax-H3-Image --prompt <text> [flags]
```

| Flag | Type | Description |
|---|---|---|
| `--prompt <text>` | string, **required** | Image description |
| `--model <model>` | string | Use `MiniMax-H3-Image` |
| `--image <path-or-url>` | string, repeatable | 1–16 reference images → image editing (`/v1/images/edits`). Order = Picture 1, 2, … |
| `--aspect-ratio <X:Y>` | string | `auto` (default) or X:Y (integers 1–300) between 1:3 and 3:1 |
| `--area <level>` | string | `1K`, `2K`, `4K` (default) |
| `--size <WxH>` | string | `auto` or e.g. `2720x1536`; area 655,360–20,000,000 px, ratio 1:3–3:1. Not with `--aspect-ratio`/`--area` |
| `--n <count>` | number | 1–10 (default: 1) |
| `--output-format <fmt>` | string | `jpg` (default), `png`, `webp` |
| `--output-compression <q>` | number | 0–100 (default 95), jpg/webp only |
| `--no-prompt-enhance` | boolean | Text-to-image only; needs `--size` or a concrete `--aspect-ratio` |
| `--response-format <format>` | string | `url` (default) or `base64`. Base64 bypasses CDN download |
| `--out-dir <dir>` | string | Download images to directory |
| `--out-prefix <prefix>` | string | Filename prefix (default: `image`) |
| `--out <path>` | string | Save a single image to an exact path |
| `--aigc-watermark` | boolean | Embed AI-generated content watermark |

H3-Image is synchronous and **not idempotent** — do not re-run a command just because it was slow; each run is billed. Partial failures exit 0 with `failed_count`/`failures` in JSON output (failures are also printed to stderr, even with `--quiet`). With `--response-format base64`, the total area `n` × W × H is limited to 20 MP for png and 80 MP for jpg/webp (`size auto` counts the `--area` level, e.g. 4K = 4096×4096).

```bash
mmx image generate --model MiniMax-H3-Image --prompt "A cat on a windowsill" --aspect-ratio 16:9 --area 2K --output json --quiet
mmx image generate --model MiniMax-H3-Image --prompt "Put the hat from Picture 2 on the person in Picture 1" --image person.jpg --image hat.png --out result.jpg --quiet
mmx image generate --model MiniMax-H3-Image --prompt "Logo" --n 3 --out-dir ./gen/ --quiet
# stdout: saved file paths (one per line)
```

---

### video generate

Generate video. Default model: `MiniMax-Hailuo-2.3` (or `MiniMax-Hailuo-2.3-Fast` for fast mode with `--image`). This is an async task — by default it polls until completion.

For `MiniMax-H3` — text-to-video, first/last-frame, multimodal reference image/video/audio generation, prompt construction, and failure handling — use the dedicated [mmx-h3-video skill](https://github.com/MiniMax-AI/cli/blob/main/skill/h3-video/SKILL.md) instead.

```bash
mmx video generate --prompt <text> [flags]
```

| Flag | Type | Description |
|---|---|---|
| `--prompt <text>` | string, **required** | Video description |
| `--model <model>` | string | `MiniMax-Hailuo-2.3` (default) or `MiniMax-Hailuo-2.3-Fast` |
| `--image <path-or-url>` | string | Input image for image-to-video |
| `--last-frame <path-or-url>` | string | Optional ending image for frame interpolation (used with `--image`) |
| `--callback-url <url>` | string | Webhook URL for completion |
| `--download <path>` | string | Save video to specific file |
| `--async` | boolean | Return task ID immediately |
| `--no-wait` | boolean | Same as `--async` |
| `--poll-interval <seconds>` | number | Polling interval (default: 5) |

```bash
# Non-blocking: get task ID
mmx video generate --prompt "A robot." --async --quiet
# stdout: {"taskId":"..."}

# Blocking: wait and get file path
mmx video generate --prompt "Ocean waves." --download ocean.mp4 --quiet
# stdout: ocean.mp4
```

### video task get

Query status of a video generation task.

```bash
mmx video task get --task-id <id> [--output json]
```

### video download

Download a completed video by task ID.

```bash
mmx video download --file-id <id> [--out <path>]
```

---

### speech synthesize

Text-to-speech. Default model: `speech-2.8-hd`. Max 10k chars.

```bash
mmx speech synthesize --text <text> [flags]
```

| Flag | Type | Description |
|---|---|---|
| `--text <text>` | string | Text to synthesize |
| `--text-file <path>` | string | Read text from file. Use `-` for stdin |
| `--model <model>` | string | `speech-2.8-hd` (default), `speech-2.6`, `speech-02` |
| `--voice <id>` | string | Voice ID (default: `English_expressive_narrator`) |
| `--speed <n>` | number | Speed multiplier |
| `--volume <n>` | number | Volume level |
| `--pitch <n>` | number | Pitch adjustment |
| `--format <fmt>` | string | Audio format (default: `mp3`) |
| `--sample-rate <hz>` | number | Sample rate (default: 32000) |
| `--bitrate <bps>` | number | Bitrate (default: 128000) |
| `--channels <n>` | number | Audio channels (default: 1) |
| `--language <code>` | string | Language boost |
| `--subtitles` | boolean | Download and save subtitles as `.srt` file (alongside `--out` audio file). API must support subtitles for the selected model.
| `--pronunciation <from/to>` | string, repeatable | Custom pronunciation |
| `--sound-effect <effect>` | string | Add sound effect |
| `--out <path>` | string | Save audio to file |
| `--stream` | boolean | Stream raw audio to stdout |

```bash
mmx speech synthesize --text "Hello world" --out hello.mp3 --quiet
# stdout: hello.mp3

mmx speech synthesize --text "Hello" --subtitles --out hello.mp3
# saves hello.mp3 + hello.srt (SRT subtitle file)

echo "Breaking news." | mmx speech synthesize --text-file - --out news.mp3
```

---

### speech transcribe

Speech-to-text. Default model: `asr-1.0`. Accepts wav, aiff, flac, m4a, mp3, aac, opus, and
ogg files up to 50 MB and 500 seconds.

```bash
mmx speech transcribe --file <path> [flags]
```

| Flag | Type | Description |
|---|---|---|
| `--file <path>` | string | Audio file to transcribe (required; also accepted as a positional argument) |
| `--model <model>` | string | `asr-1.0` (default) |
| `--response-format <fmt>` | string | `json` (default), `verbose_json`, `srt`, `vtt` |
| `--language <code>` | string | BCP-47 language hint (`zh`, `en`, `ja`, ...). Omit for automatic/mixed-language detection |
| `--timestamp-level <level>` | string | `sentence` (default) or `word`; applies to `verbose_json` / `srt` / `vtt` |
| `--stream` | boolean | Stream incremental text to stdout. Requires `--response-format json` |
| `--out <path>` | string | Write the result to a file instead of stdout |

```bash
mmx speech transcribe --file meeting.mp3
# stdout: transcript text

mmx speech transcribe --file call.mp3 --language zh --output json
# stdout: {"text":"...","duration":12.3,"trace_id":"..."}

mmx speech transcribe --file talk.mp3 --response-format verbose_json --timestamp-level word --output json
# stdout: adds n_speakers and word-level segments

mmx speech transcribe --file talk.mp3 --response-format srt --out talk.srt
# saves talk.srt; stdout: {"saved":".../talk.srt"}

mmx speech transcribe --file long.mp3 --stream
# stdout: text as it is recognized (add --output text when piping)
```

Notes:
- `mmx speech recognize` is an alias for `mmx speech transcribe`.
- `--stream` cannot be combined with `--out`; redirect stdout instead.
- `--stream` prints deltas only in text output mode. stdout that is not a terminal defaults to
  `json` (as everywhere else in this CLI), which accumulates the streamed text into one JSON
  result — pass `--output text` to pipe streamed text, e.g.
  `mmx speech transcribe --file long.mp3 --stream --output text > transcript.txt`.
- `srt` / `vtt` results are subtitle documents and are printed or saved verbatim.
- Without `--out`, `--output json` prints the full API response for `json` / `verbose_json`.
  Plain-text output prints the transcript only, so add `--output json` to read `n_speakers`
  and `segments`.
- A stream that ends without the API's final event raises a warning on stderr, since the
  transcript may be truncated.
- Input validation (missing file, unsupported format, over 50 MB, `--stream` with a non-json
  format) fails before anything is uploaded; the API stays the authority for the 500 s duration
  limit and codec support.

---

### vision describe

Image understanding via VLM. Provide either `--image` or `--file-id`, not both.

```bash
mmx vision describe (--image <path-or-url> | --file-id <id>) [flags]
```

| Flag | Type | Description |
|---|---|---|
| `--image <path-or-url>` | string | Local path or URL (auto base64-encoded) |
| `--file-id <id>` | string | Pre-uploaded file ID (skips base64) |
| `--prompt <text>` | string | Question about the image (default: `"Describe the image."`) |

```bash
mmx vision describe --image photo.jpg --prompt "What breed?" --output json
```

**stdout**: description text (text mode) or full response (json mode).

---

### search query

Web search via MiniMax.

```bash
mmx search query --q <query>
```

| Flag | Type | Description |
|---|---|---|
| `--q <query>` | string, **required** | Search query |

```bash
mmx search query --q "MiniMax AI" --output json --quiet
```

---

### quota show

Display Token Plan usage and remaining quotas.

```bash
mmx quota show [--output json]
```

---

## Tool Schema Export

Export all commands as Anthropic/OpenAI-compatible JSON tool schemas:

```bash
# All tool-worthy commands (excludes auth/config/update)
mmx config export-schema

# Single command
mmx config export-schema --command "video generate"
```

Use this to dynamically register mmx commands as tools in your agent framework.

---

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | General error |
| 2 | Usage error (bad flags, missing args) |
| 3 | Authentication error |
| 4 | Quota exceeded |
| 5 | Timeout |
| 10 | Content filter triggered |

---

## Piping Patterns

```bash
# stdout is always clean data — safe to pipe
mmx text chat --message "Hi" --output json | jq '.content'

# stderr has progress/spinners — discard if needed
mmx video generate --prompt "Waves" 2>/dev/null

# Chain: generate image → describe it
URL=$(mmx image generate --model MiniMax-H3-Image --prompt "A sunset" --quiet)
mmx vision describe --image "$URL" --quiet

# Async video workflow
TASK=$(mmx video generate --prompt "A robot" --async --quiet | jq -r '.taskId')
mmx video task get --task-id "$TASK" --output json
mmx video download --task-id "$TASK" --out robot.mp4
```

---

## Configuration Precedence

CLI flags → environment variables → `~/.mmx/config.json` → defaults.

```bash
# Persistent config
mmx config set --key region --value cn
mmx config show

# Environment
export MINIMAX_API_KEY=sk-xxxxx
export MINIMAX_REGION=cn
```

### Default Model Configuration

Set per-modality defaults so you don't need `--model` every time:

```bash
# Set defaults
mmx config set --key default-text-model --value MiniMax-M3.1-Flash
mmx config set --key default-speech-model --value speech-2.8-hd
mmx config set --key default-video-model --value MiniMax-Hailuo-2.3

# Use without --model
mmx text chat --message "Hello"
mmx speech synthesize --text "Hello" --out hello.mp3
mmx video generate --prompt "Ocean waves"

# --model still overrides per-call
mmx text chat --model MiniMax-M3.1-Flash --message "Hello"
```

**Resolution priority**: `--model` flag > config default > hardcoded fallback.
