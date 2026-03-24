#!/usr/bin/env python3
"""
MiniMax Synchronous Text-to-Speech API Client
API: POST /v1/t2a_v2

Character Limit: Maximum 10,000 characters. Use async API (text_to_audio_async.py) for longer texts.
"""

import os
import json
import base64
import warnings
from typing import Optional, Dict, Any
from pathlib import Path

# Filter urllib3 warnings about OpenSSL (macOS using LibreSSL is normal)
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

import requests


class MiniMaxTTS:
    """MiniMax Text-to-Speech Client"""

    BASE_URL = "https://api.minimaxi.com/v1/t2a_v2"
    BACKUP_URL = "https://api-bj.minimaxi.com/v1/t2a_v2"

    # Supported models
    MODELS = [
        "speech-2.8-hd",
        "speech-2.8-turbo",
        "speech-2.6-hd",
        "speech-2.6-turbo",
        "speech-02-hd",
        "speech-02-turbo",
        "speech-01-hd",
        "speech-01-turbo",
    ]

    # Supported emotions
    EMOTIONS = [
        "happy", "sad", "angry", "fearful",
        "disgusted", "surprised", "calm", "fluent", "whisper"
    ]

    # Supported audio formats
    FORMATS = ["mp3", "pcm", "flac", "wav"]

    # Supported sample rates
    SAMPLE_RATES = [8000, 16000, 22050, 24000, 32000, 44100]

    # Supported bitrates
    BITRATES = [32000, 64000, 128000, 256000]

    def __init__(self, api_key: Optional[str] = None, group_id: Optional[str] = None):
        """
        Initialize TTS client

        Args:
            api_key: MiniMax API Key, defaults to MINIMAX_API_KEY env var
            group_id: MiniMax Group ID, defaults to MINIMAX_GROUP_ID env var
        """
        raw_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.group_id = group_id or os.getenv("MINIMAX_GROUP_ID")

        if not raw_key:
            raise ValueError(
                "API key is required.\n"
                "Please set MINIMAX_API_KEY environment variable:\n"
                "  export MINIMAX_API_KEY='Bearer sk-api-xxxxx'\n"
                "Or pass api_key parameter to MiniMaxTTS()."
            )

        # Auto-add Bearer prefix if not present
        self.api_key = raw_key if raw_key.startswith("Bearer ") else f"Bearer {raw_key}"

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }
        return headers

    def synthesize(
        self,
        text: str,
        voice_id: str,
        model: str = "speech-2.8-hd",
        speed: float = 1.0,
        vol: float = 1.0,
        pitch: int = 0,
        emotion: Optional[str] = None,
        sample_rate: int = 32000,
        bitrate: int = 128000,
        format: str = "mp3",
        channel: int = 1,
        pronunciation_dict: Optional[Dict] = None,
        subtitle_enable: bool = False,
        continuous_sound: bool = False,
        output_format: str = "hex",
        language_boost: Optional[str] = None,
        voice_modify: Optional[Dict] = None,
        aigc_watermark: bool = False,
    ) -> Dict[str, Any]:
        """
        Synchronous text-to-speech (non-streaming)

        Args:
            text: Text to synthesize, length limit < 10000 characters
            voice_id: Voice ID
            model: Model version, default speech-2.8-hd
            speed: Speech speed, range [0.5, 2], default 1.0
            vol: Volume, range (0, 10], default 1.0
            pitch: Pitch, range [-12, 12], default 0
            emotion: Emotion, optional happy/sad/angry/fearful/disgusted/surprised/calm/fluent/whisper
            sample_rate: Sample rate, default 32000
            bitrate: Bitrate, default 128000
            format: Audio format, default mp3
            channel: Channel count, 1=mono, 2=stereo, default 1
            pronunciation_dict: Pronunciation dict, e.g. {"tone": ["process/(pro1)(cess2)"]}
            subtitle_enable: Enable subtitles, default False
            continuous_sound: Continuous sound optimization, only for speech-2.8 models, default False
            output_format: Output format, hex or url, default hex
            language_boost: Language boost, e.g. Chinese/English/auto
            voice_modify: Voice effects settings
            aigc_watermark: Add watermark, default False

        Returns:
            Dictionary containing audio data and metadata
        """
        if model not in self.MODELS:
            raise ValueError(f"Unsupported model: {model}. Choose from {self.MODELS}")

        if len(text) > 10000:
            raise ValueError("Text length must be < 10000 characters. Use async API for longer text.")

        payload = {
            "model": model,
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": speed,
                "vol": vol,
                "pitch": pitch,
            },
            "audio_setting": {
                "sample_rate": sample_rate,
                "bitrate": bitrate,
                "format": format,
                "channel": channel,
            },
            "subtitle_enable": subtitle_enable,
            "continuous_sound": continuous_sound,
            "output_format": output_format,
            "aigc_watermark": aigc_watermark,
        }

        if emotion and emotion in self.EMOTIONS:
            payload["voice_setting"]["emotion"] = emotion

        if pronunciation_dict:
            payload["pronunciation_dict"] = pronunciation_dict

        if language_boost:
            payload["language_boost"] = language_boost

        if voice_modify:
            payload["voice_modify"] = voice_modify

        # Try primary URL, fallback to backup URL on failure
        urls_to_try = [self.BASE_URL, self.BACKUP_URL]
        last_error = None

        for url in urls_to_try:
            try:
                response = requests.post(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()

                if result.get("base_resp", {}).get("status_code") == 0:
                    return result

                # API returned an error
                error_code = result.get("base_resp", {}).get("status_code")
                error_msg = result.get("base_resp", {}).get("status_msg", "Unknown error")

                # Authentication errors don't need retry
                if error_code == 1004:
                    raise APIError(
                        f"Authentication failed: {error_msg}\n"
                        f"Please check your API key. It should be in format: 'Bearer sk-api-xxxxx'"
                    )

                last_error = APIError(f"API Error from {url}: {error_msg} (code: {error_code})")

            except requests.exceptions.Timeout:
                last_error = APIError(f"Request to {url} timed out after 60 seconds")
            except requests.exceptions.ConnectionError as e:
                last_error = APIError(f"Connection error to {url}: {str(e)}")
            except requests.exceptions.RequestException as e:
                last_error = APIError(f"Request failed for {url}: {str(e)}")

        # All URLs failed
        raise last_error or APIError("All API endpoints failed")

        return result

    def save_audio(
        self,
        result: Dict[str, Any],
        filename: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Save audio data to file

        Args:
            result: API response dictionary
            filename: Filename (without path), default uses tts_{timestamp}.mp3
            output_dir: Output directory, default ./assets/audios

        Returns:
            Full path of saved file
        """
        if "data" not in result or "audio" not in result["data"]:
            raise ValueError("Invalid result: missing audio data")

        # Determine output path
        if output_dir is None:
            output_dir = Path.cwd() / "assets" / "audios"
        else:
            output_dir = Path(output_dir)

        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if filename is None:
            import time
            ext = result.get("extra_info", {}).get("audio_format", "mp3")
            filename = f"tts_{int(time.time())}.{ext}"

        output_path = output_dir / filename

        audio_hex = result["data"]["audio"]
        audio_bytes = bytes.fromhex(audio_hex)

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        extra_info = result.get("extra_info", {})
        print(f"Audio saved to: {output_path}")
        print(f"  Duration: {extra_info.get('audio_length', 'N/A')} ms")
        print(f"  Sample rate: {extra_info.get('audio_sample_rate', 'N/A')} Hz")
        print(f"  Size: {extra_info.get('audio_size', 'N/A')} bytes")
        print(f"  Usage characters: {extra_info.get('usage_characters', 'N/A')}")

        return str(output_path)


class APIError(Exception):
    """API Error Exception"""
    pass


def main():
    """Command-line usage example"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="MiniMax Text-to-Speech",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python3 text_to_audio.py -t "Hello world" -v tianxin_xiaoling

  # Specify output path and speed
  python3 text_to_audio.py -t "Hello world" -v male-qn-qingse -o hello.mp3 --speed 0.8

  # Add emotion
  python3 text_to_audio.py -t "Great!" -v female-shaonv --emotion happy

Common Voices:
  tianxin_xiaoling    - Female-Sweet Ling
  female-shaonv       - Female-Young
  male-qn-qingse      - Male-Youth-Innocent
  audiobook_male_1    - Audiobook Male

Environment Variables:
  MINIMAX_API_KEY     - API Key (format: Bearer sk-api-xxxxx or sk-api-xxxxx directly)
        """
    )
    parser.add_argument("--text", "-t", required=True, help="Text to synthesize")
    parser.add_argument("--voice", "-v", default="male-qn-qingse", help="Voice ID")
    parser.add_argument("--model", "-m", default="speech-2.8-hd", help="Model name")
    parser.add_argument("--output", "-o", default="output.mp3", help="Output file")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed (0.5-2.0)")
    parser.add_argument("--emotion", help="Emotion: happy/sad/angry/calm/fluent/whisper")

    args = parser.parse_args()

    try:
        client = MiniMaxTTS()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        print(f"Synthesizing text ({len(args.text)} chars)...")
        print(f"  Voice: {args.voice}")
        print(f"  Model: {args.model}")
        print(f"  Speed: {args.speed}")
        if args.emotion:
            print(f"  Emotion: {args.emotion}")

        result = client.synthesize(
            text=args.text,
            voice_id=args.voice,
            model=args.model,
            speed=args.speed,
            emotion=args.emotion
        )
        output_path = client.save_audio(result, args.output)
        print(f"\nSuccess! Audio saved to: {output_path}")

    except APIError as e:
        print(f"\nAPI Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
