# TTS Guide

## CLI usage (recommended)

```bash
# Basic
python scripts/minimax_tts.py "Hello world" -o output.mp3

# Custom voice and speed
python scripts/minimax_tts.py "你好世界" -o hi.mp3 -v female-shaonv --speed 0.9

# WAV format, high quality
python scripts/minimax_tts.py "Welcome" -o out.wav -v male-qn-jingying --format wav --sample-rate 32000

# With emotion (for speech-2.6 models)
python scripts/minimax_tts.py "Great news!" -o happy.mp3 -v female-shaonv --emotion happy --model speech-2.6-hd
```

## Programmatic usage

```python
from minimax_tts import tts

# Basic
audio_bytes = tts("Hello world")

# With options
audio_bytes = tts(
    text="Welcome to our product.",
    voice_id="female-shaonv",
    model="speech-2.8-hd",
    speed=0.9,
    fmt="mp3",
)

# Save to file
with open("output.mp3", "wb") as f:
    f.write(audio_bytes)
```

## Limits

- **Sync TTS:** max 10,000 characters per request
- **Pause markers:** insert `<#1.5#>` for a 1.5s pause (range: 0.01–99.99s)

## Model selection

| Model | Best for |
|-------|----------|
| `speech-2.8-hd` | Highest quality, auto emotion (recommended) |
| `speech-2.8-turbo` | Fast, good quality |
| `speech-2.6-hd` | Manual emotion control needed |
| `speech-2.6-turbo` | Fast + manual emotion |

## Voice selection

See [minimax-voice-catalog.md](minimax-voice-catalog.md) for the full list.

Common voices:

| Voice ID | Gender | Style |
|----------|--------|-------|
| `male-qn-qingse` | Male | Young, gentle |
| `male-qn-jingying` | Male | Elite, authoritative |
| `male-qn-badao` | Male | Dominant, powerful |
| `female-shaonv` | Female | Young, bright |
| `female-yujie` | Female | Mature, elegant |
| `female-chengshu` | Female | Sophisticated |
| `presenter_male` | Male | News presenter |
| `presenter_female` | Female | News presenter |
| `audiobook_male_1` | Male | Audiobook narrator |
| `audiobook_female_1` | Female | Audiobook narrator |

## Best practices

- Use `speech-2.8-hd` and let emotion auto-match — don't manually set emotion unless needed
- Use 32000 sample rate for web audio (good balance of quality and file size)
- For long text (>10,000 chars), split into chunks and merge with FFmpeg
