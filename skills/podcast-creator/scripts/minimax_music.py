#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
MiniMax Music Generation (HTTP)
Self-contained: no external dependencies beyond `requests`.

Usage:
  python minimax_music.py --prompt "Indie folk, melancholic" --lyrics "[verse]\nStreetlights flicker" -o song.mp3
  python minimax_music.py --prompt "Upbeat pop, energetic" --auto-lyrics -o pop.mp3
  python minimax_music.py --prompt "Jazz piano, smooth, relaxing" --instrumental -o jazz.mp3

Env: MINIMAX_API_KEY (required)
"""

import os
import sys
import json
import argparse
import requests

API_KEY = os.getenv("MINIMAX_API_KEY")
API_BASE = os.getenv("MINIMAX_API_BASE", "https://api.minimax.io/v1")


def generate_music(
    prompt: str = "",
    lyrics: str = "",
    model: str = "music-2.5+",
    is_instrumental: bool = False,
    lyrics_optimizer: bool = False,
    sample_rate: int = 44100,
    bitrate: int = 256000,
    fmt: str = "mp3",
    output_format: str = "hex",
    timeout: int = 600,
) -> dict:
    """Synchronous HTTP music generation. Returns dict with audio bytes and metadata."""
    if not API_KEY:
        raise SystemExit("ERROR: MINIMAX_API_KEY is not set.\n  export MINIMAX_API_KEY='your-key'")

    payload = {
        "model": model,
        "audio_setting": {
            "sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": fmt,
        },
        "output_format": output_format,
    }

    if prompt:
        payload["prompt"] = prompt
    if lyrics:
        payload["lyrics"] = lyrics
    if is_instrumental:
        payload["is_instrumental"] = True
    if lyrics_optimizer:
        payload["lyrics_optimizer"] = True

    resp = requests.post(
        f"{API_BASE}/music_generation",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()

    # Check API-level error
    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        raise SystemExit(f"API Error [{base_resp.get('status_code')}]: {base_resp.get('status_msg')}")

    status = data.get("data", {}).get("status")
    if status != 2:
        raise SystemExit(f"Generation incomplete (status={status}): {json.dumps(data, indent=2)}")

    audio_data = data.get("data", {}).get("audio", "")
    if not audio_data:
        raise SystemExit(f"No audio in response: {json.dumps(data, indent=2)}")

    extra = data.get("extra_info", {})

    if output_format == "hex":
        audio_bytes = bytes.fromhex(audio_data)
    else:
        # URL mode — audio_data is a URL string
        audio_bytes = None

    return {
        "audio_bytes": audio_bytes,
        "audio_url": audio_data if output_format == "url" else None,
        "duration": extra.get("music_duration"),
        "sample_rate": extra.get("music_sample_rate"),
        "channels": extra.get("music_channel"),
        "bitrate": extra.get("bitrate"),
        "size": extra.get("music_size"),
    }


def main():
    p = argparse.ArgumentParser(description="MiniMax Music Generation (HTTP)")
    p.add_argument("-o", "--output", required=True, help="Output file path")
    p.add_argument("--prompt", default="", help="Music description: style, mood, scenario (max 2000 chars)")
    p.add_argument("--lyrics", default="", help="Song lyrics with structure tags (max 3500 chars)")
    p.add_argument("--lyrics-file", default="", help="Read lyrics from file instead of --lyrics")
    p.add_argument("--model", default="music-2.5+", choices=["music-2.5+", "music-2.5"], help="Model (default: music-2.5+)")
    p.add_argument("--instrumental", action="store_true", help="Generate instrumental only (no vocals)")
    p.add_argument("--auto-lyrics", action="store_true", help="Auto-generate lyrics from prompt")
    p.add_argument("--format", default="mp3", dest="fmt", choices=["mp3", "wav", "pcm"], help="Audio format (default: mp3)")
    p.add_argument("--sample-rate", type=int, default=44100, choices=[16000, 24000, 32000, 44100], help="Sample rate (default: 44100)")
    p.add_argument("--bitrate", type=int, default=256000, choices=[32000, 64000, 128000, 256000], help="Bitrate (default: 256000)")
    args = p.parse_args()

    lyrics = args.lyrics
    if args.lyrics_file:
        with open(args.lyrics_file, "r") as f:
            lyrics = f.read()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    result = generate_music(
        prompt=args.prompt,
        lyrics=lyrics,
        model=args.model,
        is_instrumental=args.instrumental,
        lyrics_optimizer=args.auto_lyrics,
        sample_rate=args.sample_rate,
        bitrate=args.bitrate,
        fmt=args.fmt,
    )

    if result["audio_bytes"]:
        with open(args.output, "wb") as f:
            f.write(result["audio_bytes"])
        size = len(result["audio_bytes"])
    else:
        # URL mode — download
        r = requests.get(result["audio_url"], timeout=120)
        r.raise_for_status()
        with open(args.output, "wb") as f:
            f.write(r.content)
        size = len(r.content)

    duration = result.get("duration", "?")
    print(f"OK: {size} bytes -> {args.output} (duration: {duration}s)")


if __name__ == "__main__":
    main()
