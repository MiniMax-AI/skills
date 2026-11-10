#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
MiniMax Sync TTS (HTTP)
Self-contained: no external dependencies beyond `requests`.

Usage:
  python minimax_tts.py "Hello world" -o output.mp3
  python minimax_tts.py "你好世界" -o hi.mp3 -v female-shaonv --model speech-2.8-hd
  python minimax_tts.py "Welcome" -o out.wav -v male-qn-jingying --speed 0.8 --format wav

Env: MINIMAX_API_KEY (required)
"""

import os
import sys
import json
import argparse
import requests

API_KEY = os.getenv("MINIMAX_API_KEY")
API_BASE = os.getenv("MINIMAX_API_BASE", "https://api.minimax.io/v1")


def tts(
    text: str,
    voice_id: str = "male-qn-qingse",
    model: str = "speech-2.8-hd",
    speed: float = 1.0,
    volume: float = 1.0,
    pitch: int = 0,
    emotion: str = "",
    sample_rate: int = 32000,
    bitrate: int = 128000,
    fmt: str = "mp3",
    language_boost: str = "auto",
    timeout: int = 120,
) -> bytes:
    """Synchronous HTTP TTS. Returns raw audio bytes."""
    if not API_KEY:
        raise SystemExit("ERROR: MINIMAX_API_KEY is not set.\n  export MINIMAX_API_KEY='your-key'")

    voice_setting = {"voice_id": voice_id, "speed": speed, "vol": volume, "pitch": pitch}
    if emotion:
        voice_setting["emotion"] = emotion

    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "voice_setting": voice_setting,
        "audio_setting": {
            "sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": fmt,
            "channel": 1,
        },
        "language_boost": language_boost,
        "output_format": "hex",
    }

    resp = requests.post(
        f"{API_BASE}/t2a_v2",
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

    audio_hex = data.get("data", {}).get("audio", "")
    if not audio_hex:
        raise SystemExit(f"No audio in response: {json.dumps(data, indent=2)}")

    return bytes.fromhex(audio_hex)


def main():
    p = argparse.ArgumentParser(description="MiniMax Sync TTS (HTTP)")
    p.add_argument("text", help="Text to synthesize (max 10000 chars)")
    p.add_argument("-o", "--output", required=True, help="Output file path")
    p.add_argument("-v", "--voice", default="male-qn-qingse", help="Voice ID")
    p.add_argument("--model", default="speech-2.8-hd", help="Model (default: speech-2.8-hd)")
    p.add_argument("--speed", type=float, default=1.0, help="Speed 0.5-2.0")
    p.add_argument("--volume", type=float, default=1.0, help="Volume 0.1-10")
    p.add_argument("--pitch", type=int, default=0, help="Pitch -12 to 12")
    p.add_argument("--emotion", default="", help="Emotion tag (happy/sad/angry/...)")
    p.add_argument("--format", default="mp3", dest="fmt", help="Audio format (mp3/wav/flac)")
    p.add_argument("--sample-rate", type=int, default=32000, help="Sample rate")
    p.add_argument("--lang", default="auto", help="Language boost")
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    audio = tts(
        text=args.text,
        voice_id=args.voice,
        model=args.model,
        speed=args.speed,
        volume=args.volume,
        pitch=args.pitch,
        emotion=args.emotion,
        fmt=args.fmt,
        sample_rate=args.sample_rate,
        language_boost=args.lang,
    )

    with open(args.output, "wb") as f:
        f.write(audio)

    print(f"OK: {len(audio)} bytes -> {args.output}")


if __name__ == "__main__":
    main()
