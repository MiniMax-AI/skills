# MiniMax Music Playlist CN

A Chinese-optimized version of the official `minimax-music-playlist` skill, designed for users who primarily use Chinese music streaming platforms.

## Features

- **Online-first**: Supports QQ Music, NetEase Cloud Music, and Qishui Music share links
- **Cross-platform**: Works on Windows, Linux, macOS, and Docker
- **Zero dependencies**: Pure Python stdlib (urllib, json, re) — no pip install required
- **Smart genre analysis**: Uses the same `artist_genre_map.json` with 23,000+ artists including 1,400+ Chinese artists

## Differences from Official v2.0

| Aspect | Official v2.0 | CN Version |
|--------|---------------|------------|
| Data sources | Apple Music, Spotify, NetEase (local files) | QQ Music, NetEase, Qishui (online links) |
| Platform | macOS-focused | Cross-platform |
| Dependencies | Python stdlib | Python stdlib (urllib) |
| Generation | Parallel (`&` + `wait`) | Serial (more reliable) |
| Cover art | `mmx image generate` | Removed (simplified) |
| playlist.json | Save metadata | Removed (simplified) |

## Usage

Users share playlist links from Chinese music platforms:

- **QQ Music**: `https://y.qq.com/n3/other/pages/details/playlist.html?id=XXXXX`
- **NetEase**: `https://music.163.com/playlist?id=XXXXX`
- **Qishui**: `https://qishui.douyin.com/s/XXXXX/`

The skill parses the playlist, analyzes the user's taste, and generates personalized AI music using `mmx music generate`.

## Files

```
minimax-music-playlist-cn/
├── SKILL.md                 # Main skill documentation
├── playlist_parser.py       # Python parser (pure stdlib)
├── data/
│   └── artist_genre_map.json  # 23,000+ artist genre mappings
└── README.md                # This file
```

## API Endpoints

| Platform | Endpoint | Required Header |
|----------|----------|-----------------|
| QQ Music | `c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg` | `Referer: https://y.qq.com/` |
| NetEase | `music.163.com/api/v3/playlist/detail` | `Referer: https://music.163.com/` |
| Qishui | Browser rendering + JS extraction | Requires `browser_navigate` tool |

## Notes

- Qishui Music requires browser tool support (no public API)
- All `mmx` prompts should be in English for best quality
- Lyrics language follows genre (not user's UI language)
