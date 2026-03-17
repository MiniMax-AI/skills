# Music Generation Guide

## CLI Usage

```bash
# Instrumental (no vocals)
python scripts/minimax_music.py --prompt "Jazz piano, smooth, relaxing" --instrumental -o jazz.mp3

# With custom lyrics
python scripts/minimax_music.py --prompt "Indie folk, melancholic" --lyrics "[verse]\nStreetlights flicker\nOn empty roads" -o song.mp3

# Auto-generate lyrics from prompt
python scripts/minimax_music.py --prompt "Upbeat pop, energetic, summer vibes" --auto-lyrics -o pop.mp3

# From lyrics file
python scripts/minimax_music.py --prompt "Soulful blues, rainy night" --lyrics-file lyrics.txt -o blues.mp3

# Custom audio settings
python scripts/minimax_music.py --prompt "Lo-fi beats" --instrumental -o lofi.wav --format wav --sample-rate 44100 --bitrate 256000
```

## Programmatic Usage

```python
from minimax_music import generate_music

# Instrumental
result = generate_music(prompt="Jazz piano, smooth", is_instrumental=True)
with open("jazz.mp3", "wb") as f:
    f.write(result["audio_bytes"])

# With lyrics
result = generate_music(
    prompt="Indie folk, acoustic guitar",
    lyrics="[verse]\nWalking through the rain\n[chorus]\nI'll find my way home",
)

# Auto-generate lyrics
result = generate_music(
    prompt="Upbeat pop, summer anthem",
    lyrics_optimizer=True,
)

# Access metadata
print(f"Duration: {result['duration']}ms")
print(f"Sample rate: {result['sample_rate']}")
print(f"Size: {result['size']} bytes")
```

## Models

| Model | Features |
|-------|----------|
| `music-2.5+` | Recommended. Supports instrumental mode, complete song structures, hi-fi audio |
| `music-2.5` | Standard model. No instrumental mode |

## Prompt Writing

The `prompt` parameter describes music style using comma-separated descriptors:

| Category | Examples |
|----------|----------|
| Genre | Blues, Pop, Rock, Jazz, Electronic, Hip-hop, Folk, Classical |
| Mood | Soulful, Melancholy, Upbeat, Energetic, Peaceful, Dark, Nostalgic |
| Scenario | Rainy night, Summer day, Road trip, Late night, Sunrise |
| Instrumentation | Electric guitar, Piano, Acoustic, Synthesizer, Strings |
| Vocal type | Male vocals, Female vocals, Soft vocals, Powerful vocals |
| Tempo | Slow tempo, Fast tempo, Mid-tempo, Relaxed |

**Example prompts:**
```
"Soulful Blues, Rainy Night, Melancholy, Male Vocals, Slow Tempo"
"Upbeat Pop, Summer Vibes, Female Vocals, Energetic, Synth-heavy"
"Lo-fi Hip-hop, Chill, Relaxed, Instrumental, Piano samples"
"Cinematic Orchestral, Epic, Building tension, Strings and Brass"
```

## Lyrics Format

Use structure tags in brackets to organize song sections:

### Structure Tags

| Tag | Purpose |
|-----|---------|
| `[Intro]` | Opening section (can be instrumental) |
| `[Verse]` / `[Verse 1]` | Story/narrative sections |
| `[Pre-Chorus]` | Build-up before chorus |
| `[Chorus]` | Main hook, typically repeated |
| `[Post Chorus]` | Extension after chorus |
| `[Bridge]` | Contrasting section near end |
| `[Interlude]` | Instrumental break |
| `[Solo]` | Instrumental solo (add direction: "slow, bluesy") |
| `[Outro]` | Closing section |
| `[Break]` | Short pause or transition |
| `[Hook]` | Catchy repeated phrase |
| `[Build Up]` | Tension building section |
| `[Inst]` | Instrumental section |
| `[Transition]` | Section change |

### Backing Vocals & Directions

Use parentheses for backing vocals or performance notes:
```
(Ooh, yeah)
(Harmonize)
(Whispered)
(Fade out...)
```

### Example Lyrics

```
[Intro]
(Soft piano)

[Verse 1]
Streetlights flicker on empty roads
The rain keeps falling, the wind still blows
I'm walking home with nowhere to go
Just memories of what I used to know

[Pre-Chorus]
And I can feel it coming back to me
(Coming back to me)

[Chorus]
Under the neon lights tonight
I'm searching for what feels right
(Oh, feels right)
These city streets will guide me home
I'm tired of feeling so alone

[Verse 2]
Coffee shops and midnight trains
The faces change but the feeling remains
...

[Bridge]
Maybe tomorrow will be different
Maybe I'll finally understand
(Understand...)

[Solo]
(Slow, mournful, bluesy guitar)

[Outro]
(Fade out...)
Under the neon lights...
```

## Audio Settings

| Parameter | Options | Default | Notes |
|-----------|---------|---------|-------|
| `format` | mp3, wav, pcm | mp3 | WAV for highest quality |
| `sample_rate` | 16000, 24000, 32000, 44100 | 44100 | 44100 recommended |
| `bitrate` | 32000, 64000, 128000, 256000 | 256000 | Higher = better quality |

## Generation Modes

### 1. Instrumental Only
```bash
python scripts/minimax_music.py --prompt "Ambient electronic, space theme" --instrumental -o ambient.mp3
```
- Requires `music-2.5+` model
- Only `prompt` needed, no lyrics

### 2. With Custom Lyrics
```bash
python scripts/minimax_music.py --prompt "Pop ballad, emotional" --lyrics "[verse]\nYour lyrics here" -o ballad.mp3
```
- Provide both `prompt` (style) and `lyrics` (words + structure)

### 3. Auto-Generated Lyrics
```bash
python scripts/minimax_music.py --prompt "Rock anthem about freedom" --auto-lyrics -o rock.mp3
```
- System generates lyrics from prompt
- Good for quick generation when lyrics aren't critical

## Limits

- **Prompt:** max 2,000 characters
- **Lyrics:** 1–3,500 characters
- **Duration:** ~25-30 seconds per generation (varies)
- **URL expiration:** 24 hours (when using URL output mode)

## Best Practices

1. **Layer style descriptors** — Combine genre + mood + instrumentation for precise results
2. **Use structure tags** — Even simple `[verse]` `[chorus]` improves arrangement
3. **Include backing vocal cues** — `(Ooh)`, `(Yeah)` add production polish
4. **Match prompt to lyrics mood** — Conflicting prompt/lyrics produce inconsistent results
5. **Instrumental for backgrounds** — Use `--instrumental` for BGM, avoiding vocal distractions
6. **High bitrate for production** — Use 256000 for final assets, lower for drafts

## Common Use Cases

| Use Case | Command |
|----------|---------|
| Background music | `--prompt "Lo-fi, calm, ambient" --instrumental` |
| Landing page hero | `--prompt "Cinematic, inspiring, building" --instrumental` |
| Podcast intro | `--prompt "Upbeat, energetic, short" --instrumental` |
| Demo song | `--prompt "Pop, catchy" --auto-lyrics` |
| Custom jingle | `--prompt "Happy, bright, corporate" --lyrics "[hook]\nYour brand name"` |

## Error Handling

| Error Code | Meaning | Solution |
|------------|---------|----------|
| 1002 | Rate limit | Wait and retry |
| 1004 | Auth failed | Check API key |
| 1008 | Insufficient balance | Top up account |
| 1026 | Content flagged | Rephrase prompt/lyrics |
| 2013 | Invalid parameters | Check prompt/lyrics length |
