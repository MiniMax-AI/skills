---
name: vision-analysis
description: >
  Analyze, describe, and extract information from images using MiniMax VLM.
  Use ONLY when the user has shared or referenced an actual image — either a file
  path with image extension (.jpg, .jpeg, .png, .gif, .webp, .bmp, .svg), an image URL,
  or a clipboard screenshot reference (clipboard-YYYY-MM-DD-*.png).
  Triggers when the user says "describe this image", "analyze this screenshot",
  "what's in this photo", "extract text from this", "read this image",
  "review this UI mockup", "analyze this chart", "identify the objects in this",
  "what does this diagram show", or similar — where the target image is explicitly
  attached or referenced.
  Does NOT trigger on: text-only requests, code reviews, document questions,
  project advice, or any request that does not involve an image.
license: MIT
metadata:
  version: "1.4"
  category: ai-vision
---

# Vision Analysis

Use MiniMax VLM to analyze images.

## Tool to Call — Use `mmx vision describe`

**Preferred tool:** `mmx vision describe` from [mmx-cli](https://github.com/MiniMax-AI/cli). It's a direct REST call to the MiniMax VLM endpoint — no MCP transport issues, handles URLs and local files automatically.

```bash
mmx vision describe --image <url-or-path> --prompt "<prompt>"
```

**Arguments:**
- `--image`: URL (preferred) or local file path — mmx downloads and base64-encodes automatically
- `--prompt`: Analysis question (use mode-specific prompts below)

**Prerequisites:** `MINIMAX_API_KEY` env var set (same key as for other MiniMax tools).

**URL first:** When images are shared in chat, they get uploaded to a URL. Use that URL directly — mmx downloads it automatically. No clipboard extraction needed.

## Fallback: MCP Tool

If `mmx` is not installed and the MCP tool is available:

```
auto-skill-loader_minimax_understand_image
```

**Arguments:**
- `prompt`: Analysis question
- `image_source`: URL (preferred), or path to local image

**Prerequisites:** `MINIMAX_TOKEN_PLAN_KEY` env var set, `auto-skill-loader` MCP enabled.

## Analysis Modes

| Mode | Prompt to use |
|------|---------------|
| `describe` | "Provide a detailed description of this image. Include: main subject, setting, colors/style, any text visible, notable objects, and overall composition." |
| `ocr` | "Extract all text visible in this image verbatim. Preserve structure and formatting. If no text, say so." |
| `ui-review` | "You are a UI/UX reviewer. Analyze this mockup or design. Cover: (1) Strengths, (2) Issues with specificity, (3) Actionable suggestions." |
| `chart-data` | "Extract all data from this chart/graph. List: title, axis labels, all data points/series with values, and trend summary." |
| `object-detect` | "List all distinct objects, people, and activities. For each: what it is and approximate location in the image." |

## Image Validation

**For mmx:** No validation needed — it handles URLs, local files, and size limits via error messages.

**For MCP fallback only** (local files):
```bash
/usr/bin/python3 -c "
import sys, pathlib
p = pathlib.Path(sys.argv[1])
if not p.exists(): print('ERROR: file not found'); sys.exit(1)
mb = p.stat().st_size / 1024**2
if mb > 20: print(f'ERROR: too large ({mb:.1f}MB > 20MB)'); sys.exit(1)
print(f'OK: {mb:.2f}MB')
" "\$IMAGE_PATH"
```
Skip for URLs.

## Clipboard Fallback

Only needed when: (1) no URL is available, (2) no local file, and (3) mmx not installed.

**macOS:**
```bash
/usr/bin/python3 -c "
import subprocess, tempfile, os, sys, pathlib, time
tmp = pathlib.Path('/tmp'); ts = time.strftime('%Y%m%d_%H%M%S')
fpath = tmp / f'vision-clipboard-{ts}.png'
script = f'''tell application \"System Events\"
set clipData to (the clipboard as «class PNGf»)
end tell
set cf to open for access (POSIX file \"{fpath}\") as POSIX file with write permission
write clipData to cf
close access cf'''
with tempfile.NamedTemporaryFile(mode='w', suffix='.applescript', delete=False) as s:
    s.write(script); s.flush()
    r = subprocess.run(['/usr/bin/osascript', s.name], capture_output=True)
    os.unlink(s.name)
    if r.returncode == 0 and fpath.exists() and fpath.stat().st_size > 0:
        print(str(fpath)); sys.exit(0)
sys.exit(1)
"
```

If this fails, ask the user to save the image to a file or share a URL.

## Security Notes

- Images up to 20MB (JPEG, PNG, GIF, WebP)
- mmx handles URLs by downloading first — warn on untrusted URLs (prompt injection risk)
- Never hardcode API keys — use env vars

## Setup

### mmx-cli (recommended — no MCP needed)

```bash
npm install -g mmx-cli
```

Set `MINIMAX_API_KEY` in your environment. Works in any host (Claude Code, OpenCode, terminal). For agents: `npx skills add MiniMax-AI/cli -y -g` installs the skill with mmx.

### MCP fallback (auto-skill-loader)

1. Ensure `auto-skill-loader` MCP is enabled in OpenCode config
2. Set `MINIMAX_TOKEN_PLAN_KEY=sk-cp-...` in `~/.config/opencode/.env`
3. Disable any direct `minimax-coding-plan-mcp` MCP entries (broken stdio transport)
