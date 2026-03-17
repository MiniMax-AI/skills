# Getting Started

## 1. Set API key

```bash
export MINIMAX_API_KEY="<paste-your-key-here>"
```

## 2. Install dependencies

```bash
pip install requests

# FFmpeg (optional, for audio post-processing)
# macOS:
brew install ffmpeg
# Ubuntu:
sudo apt install ffmpeg
```

## 3. Quick test

```bash
python scripts/minimax_tts.py "Hello world" -o test.mp3
```

If successful, you'll see `OK: xxxxx bytes -> test.mp3`.

## Next steps

- **Voice selection**: See [minimax-voice-catalog.md](minimax-voice-catalog.md)
- **TTS workflows**: See [minimax-tts-guide.md](minimax-tts-guide.md)
- **Troubleshooting**: See [troubleshooting.md](troubleshooting.md)
