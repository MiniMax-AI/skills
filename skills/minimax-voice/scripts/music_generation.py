#!/usr/bin/env python3
"""
MiniMax Music Generation API Client
Supports generating music from lyrics and style descriptions
API: POST /v1/music_generation
"""

import os
import json
import base64
import requests
from typing import Optional, Dict, Any
from pathlib import Path


def _get_default_output_dir() -> Path:
    """Get default audio output directory"""
    return Path.cwd() / "assets" / "audios"


class MiniMaxMusicGenerator:
    """MiniMax Music Generation Client"""

    BASE_URL = "https://api.minimaxi.com/v1/music_generation"

    # Supported models
    MODELS = ["music-2.5"]

    # Supported audio formats
    FORMATS = ["mp3", "wav", "pcm"]

    # Supported sample rates
    SAMPLE_RATES = [16000, 24000, 32000, 44100]

    # Supported bitrates
    BITRATES = [32000, 64000, 128000, 256000]

    def __init__(self, api_key: Optional[str] = None, group_id: Optional[str] = None):
        """
        Initialize music generation client

        Args:
            api_key: MiniMax API Key
            group_id: MiniMax Group ID
        """
        raw_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.group_id = group_id or os.getenv("MINIMAX_GROUP_ID")

        if not raw_key:
            raise ValueError(
                "API key is required.\n"
                "Please set MINIMAX_API_KEY environment variable:\n"
                "  export MINIMAX_API_KEY='Bearer sk-api-xxxxx'\n"
                "Or pass api_key parameter to MiniMaxMusicGenerator()."
            )

        # Auto-add Bearer prefix if not present
        self.api_key = raw_key if raw_key.startswith("Bearer ") else f"Bearer {raw_key}"

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }
        if self.group_id:
            headers["X-Minimax-Group-Id"] = self.group_id
        return headers

    def generate(
        self,
        lyrics: str,
        prompt: Optional[str] = None,
        model: str = "music-2.5",
        stream: bool = False,
        output_format: str = "hex",
        sample_rate: int = 44100,
        bitrate: int = 256000,
        format: str = "mp3",
        aigc_watermark: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate music

        Args:
            lyrics: Lyrics content, use \\n to separate lines, supports [Verse], [Chorus] structure tags
            prompt: Music style description (optional for music-2.5, required for other models)
            model: Model version, default music-2.5
            stream: Stream transmission, default False
            output_format: Output format, hex or url, default hex
            sample_rate: Sample rate, default 44100
            bitrate: Bitrate, default 256000
            format: Audio format, default mp3
            aigc_watermark: Add watermark, default False

        Returns:
            Dictionary containing audio data and metadata
        """
        if model not in self.MODELS:
            raise ValueError(f"Unsupported model: {model}. Choose from {self.MODELS}")

        if len(lyrics) < 1 or len(lyrics) > 3500:
            raise ValueError("Lyrics length must be between 1 and 3500 characters")

        if prompt and len(prompt) > 2000:
            raise ValueError("Prompt length must be <= 2000 characters")

        if stream and output_format != "hex":
            raise ValueError("Streaming mode only supports hex output format")

        payload: Dict[str, Any] = {
            "model": model,
            "lyrics": lyrics,
            "stream": stream,
            "output_format": output_format,
            "audio_setting": {
                "sample_rate": sample_rate,
                "bitrate": bitrate,
                "format": format,
            },
            "aigc_watermark": aigc_watermark,
        }

        if prompt:
            payload["prompt"] = prompt

        response = requests.post(
            self.BASE_URL,
            headers=self._get_headers(),
            json=payload
        )
        response.raise_for_status()

        result = response.json()

        if result.get("base_resp", {}).get("status_code") != 0:
            raise APIError(
                f"API Error: {result['base_resp']['status_msg']} "
                f"(code: {result['base_resp']['status_code']})"
            )

        return result

    def save_audio(
        self,
        result: Dict[str, Any],
        filename: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Save generated music to file

        Args:
            result: API response dictionary
            filename: Filename (without path), default uses music_{timestamp}.mp3
            output_dir: Output directory, default ./assets/audios

        Returns:
            Full path of saved file
        """
        if "data" not in result or "audio" not in result["data"]:
            raise ValueError("Invalid result: missing audio data")

        # Determine output directory
        if output_dir is None:
            output_dir = _get_default_output_dir()
        else:
            output_dir = Path(output_dir)

        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if filename is None:
            import time
            ext = result.get("extra_info", {}).get("audio_format", "mp3")
            filename = f"music_{int(time.time())}.{ext}"

        output_path = output_dir / filename

        audio_hex = result["data"]["audio"]
        audio_bytes = bytes.fromhex(audio_hex)

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        extra_info = result.get("extra_info", {})
        print(f"Music saved to: {output_path}")
        print(f"  Duration: {extra_info.get('music_duration', 'N/A')} ms")
        print(f"  Sample rate: {extra_info.get('music_sample_rate', 'N/A')} Hz")
        print(f"  Size: {extra_info.get('music_size', 'N/A')} bytes")
        return str(output_path)

    def generate_with_structure(
        self,
        verses: list[str],
        choruses: list[str],
        prompt: str,
        bridge: Optional[str] = None,
        outro: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate music using structured lyrics

        Args:
            verses: List of verse lyrics
            choruses: List of chorus lyrics
            prompt: Music style description
            bridge: Bridge lyrics (optional)
            outro: Outro lyrics (optional)
            **kwargs: Other generate parameters

        Returns:
            API response result
        """
        lyrics_parts = []

        # Build structured lyrics
        for i, verse in enumerate(verses):
            lyrics_parts.append(f"[Verse {i+1}]")
            lyrics_parts.append(verse)

        for i, chorus in enumerate(choruses):
            lyrics_parts.append(f"[Chorus {i+1}]")
            lyrics_parts.append(chorus)

        if bridge:
            lyrics_parts.append("[Bridge]")
            lyrics_parts.append(bridge)

        if outro:
            lyrics_parts.append("[Outro]")
            lyrics_parts.append(outro)

        lyrics = "\n".join(lyrics_parts)

        return self.generate(lyrics=lyrics, prompt=prompt, **kwargs)


class APIError(Exception):
    """API Error Exception"""
    pass


def main():
    """Command-line usage example"""
    import argparse

    parser = argparse.ArgumentParser(description="MiniMax Music Generation")
    parser.add_argument("--lyrics", "-l", required=True, help="Lyrics file path or text")
    parser.add_argument("--prompt", "-p", help="Music style prompt")
    parser.add_argument("--model", "-m", default="music-2.5", help="Model name")
    parser.add_argument("--output", "-o", default="music.mp3", help="Output file")

    args = parser.parse_args()

    # Read lyrics
    if os.path.isfile(args.lyrics):
        with open(args.lyrics, "r", encoding="utf-8") as f:
            lyrics = f.read()
    else:
        lyrics = args.lyrics

    generator = MiniMaxMusicGenerator()

    print("Generating music...")
    result = generator.generate(
        lyrics=lyrics,
        prompt=args.prompt,
        model=args.model
    )

    generator.save_audio(result, args.output)
    print("Done!")


if __name__ == "__main__":
    main()
