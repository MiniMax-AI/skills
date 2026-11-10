---
name: podcast-creator
description: |
  Convert text scripts into podcast episodes using MiniMax TTS and Music APIs.
  Use when: creating podcasts from text, generating audio narration with background music,
  converting articles or blog posts to audio, producing voiceover content with intro/outro music.
  Triggers: podcast, audio episode, narration, text-to-speech with music, voiceover, audio content.
license: MIT
metadata:
  version: "1.0"
  category: creative-tools
  output_format: mp3
  sources:
    - MiniMax Text-to-Speech API (speech-2.8-hd)
    - MiniMax Music Generation API (music-2.5+)
---

# Podcast Creator

Convert text scripts into polished podcast episodes with narration and music.

## Prerequisites

Before starting, ensure:

1. **Python venv** is activated with dependencies from [requirements.txt](references/requirements.txt) installed
2. **`MINIMAX_API_KEY`** is exported (e.g. `export MINIMAX_API_KEY='your-key'`)
3. **`ffmpeg`** is available on PATH (for audio assembly)

If any prerequisite is missing, set it up first. Do NOT proceed without all three.

## Workflow

### Step 0: Collect Script

Accept the podcast script in one of three formats:

1. **Plain text** - Split into segments by blank lines or headings
2. **Markdown** - Use headings as chapter markers
3. **Structured JSON** - See [script-format.md](references/script-format.md) for the schema

If the user provides plain text or markdown, convert it to the internal JSON structure before proceeding.

Ask the user:
> "Do you have a podcast script ready, or would you like me to help write one?"

If the user wants help writing a script, ask for the topic and target length (short ~2min, medium ~5min, long ~10min), then draft chapters.

### Step 1: Voice Selection

Present voice options based on content type. Reference the [MiniMax Voice Catalog](../frontend-dev/references/minimax-voice-catalog.md) for the full list.

**Quick picks by content type:**

| Content type | Recommended voice | Voice ID |
|---|---|---|
| Tech / tutorial | Male, clear, neutral | `male-qn-qingse` |
| Storytelling | Male, warm, narrative | `male-qn-jingying` |
| News / formal | Female, professional | `female-shaonv` |
| Conversational | Female, friendly | `female-yujie` |

Ask the user:
> "Which voice style fits your podcast? Pick from the suggestions above or describe what you want."

Record the selected `voice_id` for Step 2.

### Step 2: Generate Narration

**Tool**: `scripts/minimax_tts.py`

For each chapter/segment in the script:

```bash
python3 scripts/minimax_tts.py "CHAPTER_TEXT" -o output/chapter_01.mp3 -v VOICE_ID --speed 0.95
```

**Tips:**
- Use `--speed 0.95` for narration (slightly slower than default for clarity)
- Keep each TTS call under 10,000 characters. Split longer chapters.
- Generate chapters sequentially to maintain consistent pacing.

After generation, verify each file exists:
```bash
ls -la output/chapter_*.mp3
```

### Step 3: Generate Music

**Tool**: `scripts/minimax_music.py`

Generate intro and outro music based on the podcast tone.

```bash
# Intro music (instrumental, 15-30 seconds feel)
python3 scripts/minimax_music.py --prompt "MUSIC_STYLE, short intro jingle" --instrumental -o output/intro_music.mp3

# Outro music (instrumental, fade-out feel)
python3 scripts/minimax_music.py --prompt "MUSIC_STYLE, gentle outro, fade out" --instrumental -o output/outro_music.mp3
```

**Music style examples:**
- Tech podcast: "Electronic ambient, minimal, modern, professional"
- Story podcast: "Acoustic guitar, warm, intimate, indie folk"
- News podcast: "Clean piano, confident, broadcast quality"
- Casual podcast: "Lo-fi beats, relaxed, warm, coffee shop"

### Step 4: Assemble

**Tool**: `scripts/podcast_create.py`

Stitch all audio segments into a final episode:

```bash
python3 scripts/podcast_create.py \
  --intro output/intro_music.mp3 \
  --chapters output/chapter_01.mp3 output/chapter_02.mp3 output/chapter_03.mp3 \
  --outro output/outro_music.mp3 \
  --title "Episode Title" \
  -o output/episode.mp3
```

This handles:
- Crossfading intro music into first chapter (2s overlap)
- Adding 1s silence between chapters
- Crossfading last chapter into outro music (2s overlap)
- Writing ID3 tags (title, artist) to the final mp3

### Step 5: Deliver

Output format:
1. Summary line: "Podcast episode created: {title}"
2. File path and duration
3. Chapter breakdown with timestamps

```
Podcast episode created: "Episode Title"
  File: output/episode.mp3
  Duration: 5m 23s
  Chapters:
    00:00 - Intro
    00:08 - Chapter 1: Introduction
    01:45 - Chapter 2: Main Topic
    04:10 - Chapter 3: Wrap-up
    05:05 - Outro
```

## Rules

- Always generate intro and outro music. A podcast without music sounds unfinished.
- Use `--instrumental` for all music generation. Vocals in background music compete with narration.
- Keep intro music short (the generated clip will be ~30s, but crossfading trims it naturally).
- Detect user's language and match the TTS voice language accordingly.
- All music prompts must be in **English** regardless of user language.
