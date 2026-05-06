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
  version: "2.1"
  category: creative
---

# MiniMax Music Playlist — Personalized Playlist Generator

Analyze the user's music taste, build a taste profile, generate a personalized
playlist, and create an album cover. This skill is designed for both agent and direct
user invocation — adapt interaction style to context.


## Prerequisites

- **mmx CLI** — music & image generation. Install: `npm install -g mmx-cli`. Auth: `mmx auth login --api-key <key>`.
- **Python 3** — for data parsing scripts you write on the fly (stdlib only, no pip).
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
1. Import user-exported data → 2. Build taste profile → 3. Plan playlist
→ 4. Generate songs (mmx music) → 5. Generate cover (mmx image) → 6. Play → 7. Save & feedback
```

---

## Step 1: Gather Music Listening Data

Collect the user's listening data from **user-initiated exports only**. This tool
does NOT directly query or scrape any streaming service application.

**Important:** Before processing any data, display a consent prompt:
```
This tool will analyze your exported music listening data to build a taste
profile for playlist generation. The data stays on your machine and is not
uploaded anywhere. Only the final song generation prompts (containing no
personal data) are sent to MiniMax's API.

Proceed? (y/n)
```
Only continue if the user confirms.

**Supported sources:**

| Source | Method | Data format |
|--------|--------|-------------|
| Apple Music | User exports via [Apple Privacy Portal](https://privacy.apple.com/) | CSV/JSON files in ZIP |
| Spotify | User exports via [Spotify Privacy Settings](https://www.spotify.com/account/privacy/) | JSON files in ZIP (`Streaming_History_Audio_*.json`) |
| Local music library | Read local `.mp3`/`.flac` files' ID3 metadata (user's own files) | ID3 tags |
| Manual input | User describes their taste directly | Free text |

### Apple Music data export flow

Apple provides an official data export through its privacy portal. This is the
**only** supported method for Apple Music data — do NOT use `osascript`, Music.app
AppleScript, or any other programmatic querying of Apple's applications or services.

1. Search for existing exports: `find ~ -maxdepth 4 -name "Apple_Media_Services.zip" -o -name "Apple Music - Play History.csv" -o -name "Apple Music Play Activity.csv" 2>/dev/null`
2. If found, ask the user if they want to use it
3. If not found, open Apple's privacy page: `open https://privacy.apple.com/`
4. Tell the user to:
   - Log in with their Apple Account
   - Select "Request a copy of your data"
   - Check "Apple Media Services information" (this includes Apple Music history)
   - Submit the request
5. Apple typically delivers the export within 1–7 days
6. Skip Apple Music for now and continue with other sources — tell the user they
   can re-run the playlist skill after the export arrives

**Apple Music data format:**
The export typically contains CSV files such as `Apple Music - Play History.csv`
or `Apple Music Play Activity.csv`. Key fields to extract:
- `Track Description` or `Song Name` — track name
- `Artist Name` — artist
- `Container Description` or `Album` — album name
- `Genre` — genre (if available)
- `Play Duration Milliseconds` or `Media Duration In Milliseconds` — playback duration
- `Event Start Timestamp` or `Activity date (UTC)` — timestamp

Filter out entries with very short play durations (< 30 seconds, likely skipped).

### Spotify data export flow

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

**PII stripping (mandatory):** Before any processing or caching of Spotify data,
explicitly remove the following fields from each record: `ip_addr`,
`conn_country`, `user_agent_decrypted`, `platform`, `incognito_mode`.
Use a whitelist approach — only keep the five fields listed above, discard
everything else.

### Local music library

As a fallback, read the user's local music files (`~/Music/` or user-specified
directory) and read ID3 tags (artist, title, album, genre) using Python's stdlib.
This only reads the user's own files and does not interact with any streaming service.

### Manual input

If no exports are available, ask the user to describe their taste: favorite
artists, genres, moods, and any recent songs they enjoyed.

**What to extract from each source:**
- Track names + artist names (primary signal)
- Genre tags if available
- Play counts or streaming duration if available (weight frequently played tracks higher)
- Scene/mood tags if available

**Approach:**
1. Ask which sources the user has available (Apple export, Spotify export, local files)
2. For each available source, locate and parse the exported data
3. If no sources available, fall back to manual input

**Privacy rules:**
- Never show raw track lists to the user — only show aggregated stats
- Never cache or log raw export file paths that may contain usernames
- All cached profiles must be deletable via `--purge` (see Step 7)

---

## Step 2: Build Taste Profile

From the imported data, build a taste profile covering:

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
2. If an artist is not found in the mapping table, skip it and continue

**Optional: MusicBrainz enrichment (opt-in only)**

After the local lookup is complete, if some artists could not be matched,
prompt the user:

```
Some artists in your library could not be identified using the local database.
You can enable MusicBrainz lookup to fill in the missing genre information.
MusicBrainz is a third-party open music database. Its API is free for
non-commercial use. Commercial use is subject to their license terms:
https://musicbrainz.org/doc/About/Data_License
Enable MusicBrainz lookup? (y/n)
```

Only if the user confirms, query the MusicBrainz API for unmatched artists:
   `https://musicbrainz.org/ws/2/artist/?query=artist:<n>&fmt=json`
   — extract genre tags from the response; respect rate limit (1 req/sec)
   — **must** set a descriptive User-Agent header per MusicBrainz API policy,
     e.g., `User-Agent: minimax-music-playlist/2.1 (https://github.com/your-org/repo)`
   — cache results to `<SKILL_DIR>/data/artist_cache.json` to avoid re-querying
   — if MusicBrainz returns no results for an artist, skip it

Do NOT call the MusicBrainz API without explicit user consent. The skill
must function fully without MusicBrainz — it is a supplementary data source,
not a required dependency.

**Profile caching:**
- Save profile to `<SKILL_DIR>/data/taste_profile.json`
- If a profile less than 7 days old exists, reuse it (offer rebuild option)
- If older or missing, rebuild

**Show user a summary:**
```
Your Music Profile:
  Sources: Apple Music export (230 tracks) | Spotify export (140 tracks)
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

**Data management:**
- `--purge-profile` — delete only the taste profile: `rm <SKILL_DIR>/data/taste_profile.json`
- Cached data is stored only in `<SKILL_DIR>/data/` — no data is written elsewhere
- No raw export data is ever cached — only aggregated profiles and artist metadata

---

## Replaying Playlists

If asked to play a previous playlist: `ls ~/Music/minimax-gen/playlists/`, show
available ones, and play the selected one.

---

## Notes

- **Agent vs user invocation**: The theme/scene question (Step 3) is the single
  interactive touchpoint. If the theme is already provided in the invocation,
  skip the question. Everything else runs autonomously.
- **No hardcoded scripts**: Write parsing and analysis scripts on the fly as needed.
  Use Python stdlib only. Cache results to avoid redundant work.
- **Skill directory**: `<SKILL_DIR>` = the directory containing this SKILL.md file.
  Data/cache files go in `<SKILL_DIR>/data/`.
- **All mmx prompts in English** for best generation quality.
- **No osascript / no direct app querying**: This tool does not use `osascript`,
  AppleScript, or any programmatic interface to query Music.app, Spotify.app, or
  any other streaming service application. All data come from user-initiated
  exports or local file metadata.
