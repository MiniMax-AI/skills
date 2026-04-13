---
name: minimax-music-playlist
description: >
  Generate personalized music playlists by analyzing the user's music taste
  and generation feedback history. Triggers
  on any request involving playlist generation, music taste profiling, or personalized
  music recommendations. Supports multilingual triggers — match equivalent phrases in
  any language.
license: MIT
metadata:
  version: "2.0"
  category: creative
---

# MiniMax Music Playlist — Personalized Playlist Generator

Scan the user's music taste, build a taste profile, generate a personalized
playlist, and create an album cover. This skill is designed for both agent and direct
user invocation — adapt interaction style to context.

## Prerequisites

- **mmx CLI** — music & image generation. Install: `npm install -g mmx-cli`. Auth: `mmx auth login --api-key <key>`.
- **Python 3** — for scanning scripts you write on the fly (stdlib only, no pip).
- **Audio player** — `mpv`, `ffplay`, or `afplay` (macOS built-in).

## Language

Detect the user's language from their message. **All user-facing text must be
in the same language as the user's prompt** — do not mix languages. If the user
writes in Chinese, all output (profile summary, theme suggestions, playlist plan,
playback info) must be fully in Chinese. If in English, all in English.

All `mmx` generation prompts should be in English for best quality.
Each song's lyrics language follows its genre (K-pop → Korean, J-pop → Japanese, etc.),
NOT the user's UI language.

---

## Workflow

```
1. Scan local music apps → 2. Build taste profile → 3. Plan playlist
→ 4. Generate songs (mmx music) → 5. Generate cover (mmx image) → 6. Play → 7. Save & feedback
```

---

## Step 1: Gather Music Listening Data

Collect the user's listening data from available sources.

**Supported sources:**

| Source | Method | Data format |
|--------|--------|-------------|
| Apple Music | `osascript` to query Music.app (official AppleScript interface) | Track name, artist, album, genre, play count |
| Spotify | User exports their own data via [Spotify Privacy Settings](https://www.spotify.com/account/privacy/) | JSON files in ZIP (`Streaming_History_Audio_*.json`) |
| Manual input | User describes their taste directly | Free text |

**Spotify data export flow:**
Spotify does not store useful data locally. To include Spotify listening history,
first check if the user already has a Spotify data export:

1. Search for existing exports: `find ~ -maxdepth 4 -name "my_spotify_data.zip" -o -name "Streaming_History_Audio_*.json" 2>/dev/null`
2. If found, ask the user if they want to use it
3. If ZIP, unzip and locate `Spotify Extended Streaming History/Streaming_History_Audio_*.json`
4. If not found, open the Spotify privacy page: `open https://www.spotify.com/account/privacy/`
5. Tell the user to log in, scroll to "Download your data", and click "Request data"
6. Skip Spotify for now and continue with other sources — tell the user they can
   re-run the playlist skill after the data export arrives (usually a few days)

**Spotify data format:**
The export contains `Streaming_History_Audio_YYYY.json` files (one per year), each
is a JSON array of listening events. Key fields to extract:
- `master_metadata_album_artist_name` — artist name
- `master_metadata_track_name` — track name
- `master_metadata_album_album_name` — album name
- `ms_played` — playback duration in milliseconds (use as weight: longer = stronger signal)
- `ts` — timestamp

Filter out entries where `ms_played < 30000` (less than 30 seconds, likely skipped).
Do NOT use or store `ip_addr` or other sensitive fields.

**What to extract from each source:**
- Track names + artist names (primary signal)
- Playlist names and membership (e.g., a playlist named "Chinese Traditional" tells you genre preference)
- Play counts or streaming duration if available (weight frequently played tracks higher)
- Scene/mood tags if available

**Approach:**
1. Check if Apple Music is available (try `osascript` query)
2. Ask if the user has a Spotify data export ZIP to provide
3. If no sources available, ask the user to describe their taste manually

**Privacy rule:** Never show raw track lists to the user. Only show aggregated stats.

---

## Step 2: Build Taste Profile

From the scanned data, build a taste profile covering:

- **Genre distribution** — what styles the user listens to (e.g., J-pop 20%, R&B 15%, Classical 10%)
- **Mood tendencies** — emotional tone preferences (melancholic, energetic, calm, romantic, etc.)
- **Vocal preference** — male vs female voice ratio
- **Tempo preference** — slow / moderate / upbeat / fast distribution
- **Language distribution** — zh, en, ja, ko, etc.
- **Top artists** — most listened artists

**How to infer genre/mood from artist names:**
Most raw data only has artist + track names without genre tags. To enrich this:
1. Look up artists in the local mapping table at `<SKILL_DIR>/data/artist_genre_map.json`
   — this table covers 20,000 popular artists with pre-mapped genres, vocal type, and language
2. For artists not in the mapping table, query the MusicBrainz API:
   `https://musicbrainz.org/ws/2/artist/?query=artist:<name>&fmt=json`
   — extract genre tags from the response; respect rate limit (1 req/sec)
   — cache results to `<SKILL_DIR>/data/artist_cache.json` to avoid re-querying
3. If MusicBrainz returns no results, skip the artist

**Profile caching:**
- Save profile to `<SKILL_DIR>/data/taste_profile.json`
- If a profile less than 7 days old exists, reuse it (offer rescan option)
- If older or missing, rebuild

**Show user a summary:**
```
Your Music Profile:
  Sources: Apple Music 230 | Spotify 140
  Genres: J-pop 20% | R&B 15% | Classical 10% | Indie Pop 9%
  Moods: Melancholic 25% | Calm 20% | Romantic 18%
  Vocals: Female 65% | Male 35%
  Top artists: Faye Wong, Ryuichi Sakamoto, Taylor Swift, Jay Chou, Taeko Onuki
```

If invoked by an agent with clear parameters, skip the confirmation and proceed.
If invoked by a user directly, ask if the profile looks right before continuing.

---

## Step 3: Plan Playlist

**Ask the user for a theme/scene before generating.** This is the one
interactive step in the workflow. All other steps run autonomously.

If the theme was already provided in the invocation (e.g., the agent or user
said "generate a late night chill playlist"), use it directly and skip the question.
Otherwise, ask:

```
What theme would you like for your playlist? Here are some suggestions:

- "Late night chill" — relaxing slow songs
- "Commute" — upbeat and energizing
- "Rainy day" — melancholic & cozy
- "Surprise me" — random based on your taste

Or tell me your own vibe!
```

Once the user picks a theme, proceed automatically through generation, cover,
playback, and saving — no further confirmations needed.

Determine playlist parameters:
- **Theme/mood** — from user input, or default to top mood from profile
- **Song count** — from user input, or default to 5
- **Genre mix** — weighted by profile, with variety

**Per-song lyrics language** follows genre:

| Genre | Lyrics language |
|-------|----------------|
| K-pop, Korean R&B/ballad | Korean |
| J-pop, city pop, J-rock | Japanese |
| C-pop, Chinese-style, Mandopop | Chinese |
| Western pop/indie/rock/jazz/R&B | English |
| Latin pop, bossa nova | Spanish/Portuguese |
| Instrumental, lo-fi, ambient | No lyrics (`--instrumental`) |

Embed language naturally into the mmx prompt via vocal description:
- Good: `"A melancholy Chinese R&B ballad with a gentle introspective male voice, electric piano, bass, slow tempo"`
- Bad: `"R&B ballad, melancholy... sung in Chinese"`

**Show the playlist plan before generating.** Display each song with two lines:
the first line shows genre, mood, and vocal/language tag; the second line shows
a short description of the song. **All user-facing text (plan, descriptions, moods,
labels) must be in the same language as the user's prompt.** Only the actual `--prompt`
passed to `mmx` should be in English — this is internal and should NOT be shown to
the user. Example:

```
Playlist Plan: Late Night Chill (5 songs)

1. Neo-soul R&B — introspective  English/male vocal
   A mellow neo-soul R&B ballad with warm baritone, electric piano, smooth bass

2. Lo-fi hip-hop — dreamy  Instrumental
   Dreamy lo-fi with sampled piano, vinyl crackle, soft electronic drums

3. Smooth jazz — romantic  English/female vocal
   Silky female voice, saxophone, piano, romantic starlit night

4. Indie folk — melancholic  English/male vocal
   Tender male voice, acoustic guitar, harmonica, quiet solitude

5. Ambient electronic — calm  Instrumental
   Soft synth pads, gentle arpeggios, dreamy atmosphere
```

After showing the plan, proceed directly to generation — no confirmation needed.
The user has already chosen the theme; the plan is shown for transparency, not approval.

---

## Step 4: Generate Songs

Use `mmx music generate` to create all songs. **Generate concurrently** (up to 5 in parallel).

```bash
# Example: 5 songs in parallel
mmx music generate --prompt "<english_prompt_1>" --lyrics-optimizer \
  --out ~/Music/minimax-gen/playlists/<name>/01_desc.mp3 --quiet --non-interactive &
mmx music generate --prompt "<english_prompt_2>" --instrumental \
  --out ~/Music/minimax-gen/playlists/<name>/02_desc.mp3 --quiet --non-interactive &
# ... more songs ...
wait
```

**Key flags:**
- `--lyrics-optimizer` — auto-generate lyrics from prompt (for vocal tracks)
- `--instrumental` — no vocals
- `--vocals "<description>"` — vocal style (e.g., "warm Chinese male baritone")
- `--genre`, `--mood`, `--tempo`, `--instruments` — fine-grained control
- `--quiet --non-interactive` — suppress interactive output for batch mode
- `--out <path>` — save to file

**File naming:** `<NN>_<short_desc>.mp3` (e.g., `01_rnb_midnight.mp3`)

**Output directory:** `~/Music/minimax-gen/playlists/<playlist_name>/`

If a song fails, **retry once** before skipping. Log the error and continue with the rest.

---

## Step 5: Generate Album Cover

Generate the album cover **concurrently with the songs** (Step 4), not after.
Launch the `mmx image generate` call in parallel with the song generation calls.

Craft a prompt that reflects the playlist's theme, mood, and genre mix. The image
should feel like an album cover — artistic, evocative, not literal.

```bash
mmx image generate \
  --prompt "<cover description based on playlist theme and mood>" \
  --aspect-ratio 1:1 \
  --out-dir ~/Music/minimax-gen/playlists/<playlist_name>/ \
  --out-prefix cover \
  --quiet
```

**Prompt guidance:**
- Abstract/artistic style works best for album covers
- Reference the dominant mood and genre (e.g., "dreamy late-night cityscape, neon reflections, lo-fi aesthetic")
- Do NOT include text or song titles in the image prompt
- Aspect ratio should be 1:1 (square, standard album cover)

---

## Step 6: Playback

Detect an available player and play the playlist in order:

| Player | Command | Controls |
|--------|---------|----------|
| mpv | `mpv --no-video <file>` | `q` skip, Space pause, arrows seek |
| ffplay | `ffplay -nodisp -autoexit <file>` | `q` skip |
| afplay | `afplay <file>` | Ctrl+C skip |

Play all `.mp3` files in the playlist directory in filename order.
Only play the songs generated in this session — if the directory has old files
from a previous run, clean them out first or filter by the known filenames.
If no player is found, just show the file paths.

---

## Step 7: Save & Feedback

Save playlist metadata to `<playlist_dir>/playlist.json`:
```json
{
  "name": "Late Night Chill",
  "theme": "late night chill",
  "created_at": "2026-04-11T22:00:00",
  "song_count": 5,
  "cover": "cover_001.png",
  "songs": [
    {"index": 1, "filename": "01_rnb_midnight.mp3", "prompt": "...", "rating": null}
  ]
}
```

If the user is present, ask for feedback (per-song or overall). Update the
taste profile's feedback section with liked/disliked genres and prompts to
improve future playlists.

---

## Replaying Playlists

If asked to play a previous playlist: `ls ~/Music/minimax-gen/playlists/`, show
available ones, and play the selected one.

---

## Notes

- **Agent vs user invocation**: The theme/scene question (Step 3) is the single
  interactive touchpoint. If the theme is already provided in the invocation,
  skip the question. Everything else runs autonomously.
- **No hardcoded scripts**: Write scanning/analysis scripts on the fly as needed.
  Use Python stdlib only. Cache results to avoid redundant work.
- **Skill directory**: `<SKILL_DIR>` = the directory containing this SKILL.md file.
  Data/cache files go in `<SKILL_DIR>/data/`.
- **All mmx prompts in English** for best generation quality.
