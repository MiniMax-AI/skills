---
name: minimax-voice
description: MiniMax voice synthesis and music generation API toolkit. Supports text-to-speech (sync/async), voice management (query/clone/design), and music generation. Use this skill when users need voice synthesis, voice cloning, or music generation.
---

# MiniMax Voice Toolkit

Python client toolkit for MiniMax voice synthesis and music generation APIs.

## Environment Variables

**⚠️ Important: Before each use, check if the API Key environment variable is set. If not, configure it first before calling the scripts.**

```bash
export MINIMAX_API_KEY="your_api_key_here"
```

**Default Output Directory**: All generated audio files are automatically saved to `./assets/audios/` (auto-created)

## Scripts

| Script | Function | API |
|-----|------|-----|
| `scripts/text_to_audio.py` | Synchronous TTS | `/v1/t2a_v2` |
| `scripts/text_to_audio_async.py` | Asynchronous TTS | `/v1/t2a_async_v2` |
| `scripts/voice_manager.py` | Voice Management | `/v1/get_voice`, `/v1/voice_clone`, `/v1/voice_design` |
| `scripts/music_generation.py` | Music Generation | `/v1/music_generation` |

## Character Limits

| Script | Character Limit | Use Case |
|------|---------|---------|
| `text_to_audio.py` (sync) | ≤ 10,000 chars | Short text, real-time synthesis |
| `text_to_audio_async.py` (async) | 10,001 - 50,000 chars | Long text, audiobooks |

**Note**: Texts exceeding 50,000 characters need to be split into multiple requests.

## Usage Examples

```bash
# Synchronous TTS (≤ 10000 chars)
python3 scripts/text_to_audio.py -t "Hello" -v male-qn-qingse -o output.mp3

# Asynchronous TTS (10001-50000 chars)
python3 scripts/text_to_audio_async.py -t "Long text..." -v audiobook_male_1 -w -o output.mp3

# List voices
python3 scripts/voice_manager.py list

# Clone voice
python3 scripts/voice_manager.py clone --file voice.mp3 --voice-id MyVoice001

# Design voice
python3 scripts/voice_manager.py design --prompt "Warm female voice" --preview "Preview text" -o trial.mp3

# Generate music
python3 scripts/music_generation.py -l lyrics.txt -p "Pop music, upbeat" -o song.mp3
```

## Supported Models

### Text-to-Speech
- `speech-2.8-hd` - Latest HD model, supports interjection tags
- `speech-2.8-turbo` - Latest high-speed model

### Music Generation
- `music-2.5` - Latest music generation model

## Common Voice IDs

- `male-qn-qingse` - Male-Youth-Innocent
- `female-shaonv` - Female-Young
- `tianxin_xiaoling` - Female-Sweet Ling
- `audiobook_male_1` - Audiobook Male
- `Chinese (Mandarin)_News_Anchor` - News Anchor

Full list available via `voice_manager.list_voices()`.

## Error Codes

- `0` - Success
- `1000` - Unknown error
- `1001` - Timeout
- `1002` - Rate limit triggered
- `1004` - Authentication failed
- `1008` - Insufficient balance
- `2013` - Parameter error
- `2038` - No cloning permission
