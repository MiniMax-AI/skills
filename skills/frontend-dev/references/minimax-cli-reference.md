# Provider Reference — MiniMax

All asset generation uses MiniMax API. Env: `MINIMAX_API_KEY` (required).

## Audio (Sync TTS)

**Script:** `scripts/minimax_tts.py`

```bash
python scripts/minimax_tts.py "Hello world" -o output.mp3
python scripts/minimax_tts.py "你好" -o hi.mp3 -v female-shaonv
python scripts/minimax_tts.py "Welcome" -o out.wav -v male-qn-jingying --speed 0.8 --format wav
```

**Model:** `speech-2.8-hd` (default).

| Flag | Default | Range / Options |
|------|---------|-----------------|
| `-o` | (required) | Output file path |
| `-v` | `male-qn-qingse` | Voice ID |
| `--model` | `speech-2.8-hd` | speech-2.8-hd / speech-2.8-turbo / speech-2.6-hd / speech-2.6-turbo |
| `--speed` | 1.0 | 0.5–2.0 |
| `--volume` | 1.0 | 0.1–10 |
| `--pitch` | 0 | -12 to 12 |
| `--emotion` | (auto) | happy / sad / angry / fearful / disgusted / surprised / calm / fluent / whisper |
| `--format` | mp3 | mp3 / wav / flac |
| `--lang` | auto | Language boost |

**Programmatic:**
```python
from minimax_tts import tts
audio_bytes = tts("Hello", voice_id="female-shaonv")
```


## Video (Text-to-Video)

**Script:** `scripts/minimax_video.py`

```bash
python scripts/minimax_video.py "A cat playing piano" -o cat.mp4
python scripts/minimax_video.py "Ocean waves [Truck left]" -o waves.mp4 --duration 10
python scripts/minimax_video.py "City skyline [Push in]" -o city.mp4 --resolution 1080P
```

**Model:** `MiniMax-Hailuo-2.3` (default). Async: script handles create → poll → download automatically.

| Flag | Default | Options |
|------|---------|---------|
| `-o` | (required) | Output file path (.mp4) |
| `--model` | `MiniMax-Hailuo-2.3` | MiniMax-Hailuo-2.3 / MiniMax-Hailuo-02 / T2V-01-Director / T2V-01 |
| `--duration` | 6 | 6 / 10 (10s only at 768P with Hailuo models) |
| `--resolution` | 768P | 720P / 768P / 1080P (1080P only 6s) |
| `--no-optimize` | false | Disable prompt auto-optimization |
| `--poll-interval` | 10 | Seconds between status checks |
| `--max-wait` | 600 | Max wait time in seconds |

**Camera commands** — insert `[Command]` in prompt: `[Push in]`, `[Truck left]`, `[Pan right]`, `[Zoom out]`, `[Static shot]`, `[Tracking shot]`, etc.

**Programmatic:**
```python
from minimax_video import generate
generate("A cat playing piano", "cat.mp4", model="MiniMax-Hailuo-2.3", duration=6)
```

See [minimax-video-guide.md](minimax-video-guide.md) for full camera command list and model compatibility.

## Image (Text-to-Image)

**Script:** `scripts/minimax_image.py`

```bash
python scripts/minimax_image.py "A cat astronaut in space" -o cat.png
python scripts/minimax_image.py "Mountain landscape" -o hero.png --ratio 16:9
python scripts/minimax_image.py "Product icons, flat style" -o icons.png -n 4 --seed 42
```

**Model:** `image-01`. Sync: returns image URL (or base64) immediately.

| Flag | Default | Options |
|------|---------|---------|
| `-o` | (required) | Output file path (.png/.jpg) |
| `--ratio` | 1:1 | 1:1 / 16:9 / 4:3 / 3:2 / 2:3 / 3:4 / 9:16 / 21:9 |
| `-n` | 1 | Number of images (1–9) |
| `--seed` | (random) | Seed for reproducibility |
| `--optimize` | false | Enable prompt auto-optimization |
| `--base64` | false | Return base64 instead of URL |

**Batch output:** with `-n > 1`, files are named `out-0.png`, `out-1.png`, etc.

**Programmatic:**
```python
from minimax_image import generate_image, download_and_save
result = generate_image("A cat in space", aspect_ratio="16:9")
download_and_save(result["data"]["image_urls"][0], "cat.png")
```

See [minimax-image-guide.md](minimax-image-guide.md) for ratio dimensions and details.

## Music (Text-to-Music)

**Script:** `scripts/minimax_music.py`

```bash
python scripts/minimax_music.py --prompt "Indie folk, melancholic" --lyrics "[verse]\nStreetlights flicker" -o song.mp3
python scripts/minimax_music.py --prompt "Upbeat pop, energetic" --auto-lyrics -o pop.mp3
python scripts/minimax_music.py --prompt "Jazz piano, smooth, relaxing" --instrumental -o jazz.mp3
```

**Model:** `music-2.5+` (default). Sync: returns audio hex or URL.

| Flag | Default | Options |
|------|---------|---------|
| `-o` | (required) | Output file path (.mp3/.wav) |
| `--prompt` | (empty) | Music description: style, mood, scenario (max 2000 chars) |
| `--lyrics` | (empty) | Song lyrics with structure tags (max 3500 chars) |
| `--lyrics-file` | (empty) | Read lyrics from file |
| `--model` | `music-2.5+` | music-2.5+ / music-2.5 |
| `--instrumental` | false | Generate instrumental only (no vocals, music-2.5+ only) |
| `--auto-lyrics` | false | Auto-generate lyrics from prompt |
| `--format` | mp3 | mp3 / wav / pcm |
| `--sample-rate` | 44100 | 16000 / 24000 / 32000 / 44100 |
| `--bitrate` | 256000 | 32000 / 64000 / 128000 / 256000 |

**Lyrics structure tags:** `[Intro]`, `[Verse]`, `[Pre Chorus]`, `[Chorus]`, `[Interlude]`, `[Bridge]`, `[Outro]`, `[Post Chorus]`, `[Transition]`, `[Break]`, `[Hook]`, `[Build Up]`, `[Inst]`, `[Solo]`

**Programmatic:**
```python
from minimax_music import generate_music
result = generate_music(prompt="Jazz piano", is_instrumental=True)
with open("jazz.mp3", "wb") as f:
    f.write(result["audio_bytes"])
```
