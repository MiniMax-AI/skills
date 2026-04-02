# TTS Guide

## Setup

```bash
cd skills/MiniMaxStudio
pip install -r requirements.txt
brew install ffmpeg   # macOS (or: sudo apt install ffmpeg)
export MINIMAX_API_KEY="your-api-key"   # sk-api-xxx or sk-cp-xxx
python scripts/check_environment.py
```

## Quick Test

```bash
python scripts/tts/generate_voice.py tts "Hello, this is a test." -o test.mp3
```

## Voice Management

List available voices:

```bash
python scripts/tts/generate_voice.py list-voices
```

### Voice Cloning

Create a custom voice from an audio sample:

```bash
python scripts/tts/generate_voice.py clone audio.mp3 --voice-id my-custom-voice

# With preview
python scripts/tts/generate_voice.py clone audio.mp3 --voice-id my-voice --preview "Test text" --preview-output preview.mp3
```

Requirements: 10s–5min duration, ≤20MB, mp3/wav/m4a format.

### Voice Design

Design a voice from a text description:

```bash
python scripts/tts/generate_voice.py design "A warm, gentle female voice" --voice-id designed-voice
```

Custom voices expire after 7 days if not used with TTS.

## Audio Processing

### Merge

```bash
python scripts/tts/generate_voice.py merge file1.mp3 file2.mp3 -o combined.mp3
python scripts/tts/generate_voice.py merge a.mp3 b.mp3 -o merged.mp3 --crossfade 300
```

### Convert

```bash
python scripts/tts/generate_voice.py convert input.wav -o output.mp3
python scripts/tts/generate_voice.py convert input.wav -o output.mp3 --format mp3 --bitrate 192k --sample-rate 32000
```

FFmpeg required. Supported formats: mp3, wav, flac, ogg, m4a, aac, wma, opus, pcm.

## Segment-Based TTS

For multi-voice, multi-emotion workflows using a `segments.json` file:

```bash
# Validate
python scripts/tts/generate_voice.py validate segments.json --verbose

# Generate
python scripts/tts/generate_voice.py generate segments.json -o output.mp3 --crossfade 200
```

### segments.json Format

```json
[
  { "text": "Hello!", "voice_id": "female-shaonv", "emotion": "" },
  { "text": "How are you?", "voice_id": "male-qn-qingse", "emotion": "happy" }
]
```

- `text` (required): Text to synthesize
- `voice_id` (required): Voice ID
- `emotion` (optional): For speech-2.8 models, leave empty for auto-matching. Valid values: happy, sad, angry, fearful, disgusted, surprised, calm, fluent, whisper

## Troubleshooting

| Error | Solution |
|-------|----------|
| `MINIMAX_API_KEY is required` | `export MINIMAX_API_KEY="key"` |
| `FFmpeg not installed` | `brew install ffmpeg` |
| `Voice not found` | `python scripts/tts/generate_voice.py list-voices` |
| `401 Unauthorized` | Check API key validity |
| `429 Too Many Requests` | Add delays between requests |

## API Details

- **Endpoint**: `POST /v1/t2a_v2`
- **Base URL**: `https://api.minimaxi.com`
- **Auth**: `Authorization: Bearer {MINIMAX_API_KEY}`
- **Models**: speech-2.8-hd (recommended), speech-2.8-turbo
- **Text limit**: 10,000 characters per request
- **Pause marker**: `<#x#>` where x is seconds (0.01–99.99)
- **Interjection tags** (speech-2.8 only): `(laughs)`, `(chuckle)`, `(coughs)`, `(sighs)`, `(breath)`, etc.
