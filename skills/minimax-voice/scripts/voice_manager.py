#!/usr/bin/env python3
"""
MiniMax Voice Management API Client
Supports voice query, voice cloning, voice design, file upload
APIs:
- POST /v1/get_voice (Query voices)
- POST /v1/voice_clone (Voice cloning)
- POST /v1/voice_design (Voice design)
- POST /v1/files/upload (File upload)
"""

import os
import json
import base64
import requests
from typing import Optional, Dict, Any, List, Union
from pathlib import Path


def _get_default_output_dir() -> Path:
    """Get default audio output directory"""
    return Path.cwd() / "assets" / "audios"


class MiniMaxVoiceManager:
    """MiniMax Voice Management Client"""

    BASE_URL = "https://api.minimaxi.com"

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

    # Sound effect options
    SOUND_EFFECTS = [
        "spacious_echo",      # Spacious echo
        "auditorium_echo",    # Auditorium broadcast
        "lofi_telephone",     # Telephone distortion
        "robotic",            # Robotic/electronic
    ]

    def __init__(self, api_key: Optional[str] = None, group_id: Optional[str] = None):
        """
        Initialize voice management client

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
                "Or pass api_key parameter to MiniMaxVoiceManager()."
            )

        # Auto-add Bearer prefix if not present
        self.api_key = raw_key if raw_key.startswith("Bearer ") else f"Bearer {raw_key}"

    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Authorization": self.api_key
        }
        if content_type:
            headers["Content-Type"] = content_type
        if self.group_id:
            headers["X-Minimax-Group-Id"] = self.group_id
        return headers

    # ============ Voice Query ============

    def list_voices(
        self,
        voice_type: str = "all"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query available voices

        Args:
            voice_type: Voice type, options system/voice_cloning/voice_generation/all

        Returns:
            Dictionary containing various voice types
        """
        if voice_type not in ["system", "voice_cloning", "voice_generation", "all"]:
            raise ValueError(f"Invalid voice_type: {voice_type}")

        response = requests.post(
            f"{self.BASE_URL}/v1/get_voice",
            headers=self._get_headers(),
            json={"voice_type": voice_type}
        )
        response.raise_for_status()

        result = response.json()

        if result.get("base_resp", {}).get("status_code") != 0:
            raise APIError(
                f"API Error: {result['base_resp']['status_msg']} "
                f"(code: {result['base_resp']['status_code']})"
            )

        return {
            "system": result.get("system_voice", []),
            "voice_cloning": result.get("voice_cloning", []),
            "voice_generation": result.get("voice_generation", []),
        }

    def get_system_voices(self) -> List[Dict[str, Any]]:
        """Get system voice list"""
        return self.list_voices("system")["system"]

    def get_cloned_voices(self) -> List[Dict[str, Any]]:
        """Get cloned voice list"""
        return self.list_voices("voice_cloning")["voice_cloning"]

    def get_generated_voices(self) -> List[Dict[str, Any]]:
        """Get text-to-voice list"""
        return self.list_voices("voice_generation")["voice_generation"]

    # ============ File Upload ============

    def upload_voice_clone_file(
        self,
        file_path: Union[str, Path],
        purpose: str = "voice_clone"
    ) -> Dict[str, Any]:
        """
        Upload voice cloning audio file

        Args:
            file_path: Audio file path
            purpose: File purpose, voice_clone or prompt_audio

        Returns:
            Dictionary containing file_id
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "audio/mpeg")}
            data = {"purpose": purpose}

            response = requests.post(
                f"{self.BASE_URL}/v1/files/upload",
                headers=self._get_headers(content_type=""),
                data=data,
                files=files
            )

        response.raise_for_status()
        result = response.json()

        if result.get("base_resp", {}).get("status_code") != 0:
            raise APIError(
                f"API Error: {result['base_resp']['status_msg']} "
                f"(code: {result['base_resp']['status_code']})"
            )

        file_obj = result.get("file", {})
        return {
            "file_id": file_obj.get("file_id"),
            "bytes": file_obj.get("bytes"),
            "filename": file_obj.get("filename"),
            "created_at": file_obj.get("created_at"),
        }

    def upload_prompt_audio(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Upload sample audio (for enhanced cloning effect)

        Args:
            file_path: Audio file path (must be < 8 seconds)

        Returns:
            Dictionary containing file_id
        """
        return self.upload_voice_clone_file(file_path, purpose="prompt_audio")

    # ============ Voice Cloning ============

    def clone_voice(
        self,
        file_id: Union[str, int],
        voice_id: str,
        text: Optional[str] = None,
        model: Optional[str] = None,
        clone_prompt: Optional[Dict] = None,
        language_boost: Optional[str] = None,
        need_noise_reduction: bool = False,
        need_volume_normalization: bool = False,
        aigc_watermark: bool = False,
        continuous_sound: bool = False,
    ) -> Dict[str, Any]:
        """
        Quick voice cloning

        Args:
            file_id: Uploaded audio file ID
            voice_id: Custom voice ID (8-256 chars, starts with letter, allows alphanumeric, -, _)
            text: Preview text (optional, generates preview audio if provided)
            model: Model for preview (required when text is provided)
            clone_prompt: Sample audio config {"prompt_audio": file_id, "prompt_text": text}
            language_boost: Language boost
            need_noise_reduction: Enable noise reduction
            need_volume_normalization: Enable volume normalization
            aigc_watermark: Add watermark
            continuous_sound: Continuous sound optimization

        Returns:
            Cloning result, includes demo_audio (if preview provided)
        """
        if text and not model:
            raise ValueError("model is required when text is provided for preview")

        if model and model not in self.MODELS:
            raise ValueError(f"Unsupported model: {model}")

        payload: Dict[str, Any] = {
            "file_id": int(file_id),
            "voice_id": voice_id,
            "need_noise_reduction": need_noise_reduction,
            "need_volume_normalization": need_volume_normalization,
            "aigc_watermark": aigc_watermark,
            "continuous_sound": continuous_sound,
        }

        if text:
            payload["text"] = text
            payload["model"] = model

        if clone_prompt:
            payload["clone_prompt"] = clone_prompt

        if language_boost:
            payload["language_boost"] = language_boost

        response = requests.post(
            f"{self.BASE_URL}/v1/voice_clone",
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

        return {
            "voice_id": voice_id,
            "demo_audio": result.get("demo_audio"),
            "input_sensitive": result.get("input_sensitive"),
        }

    # ============ Voice Design ============

    def design_voice(
        self,
        prompt: str,
        preview_text: str,
        voice_id: Optional[str] = None,
        aigc_watermark: bool = False,
    ) -> Dict[str, Any]:
        """
        Voice design (text-to-voice)

        Args:
            prompt: Voice description text
            preview_text: Preview audio text
            voice_id: Custom voice ID (optional, auto-generated if not provided)
            aigc_watermark: Add watermark

        Returns:
            Dictionary containing voice_id and trial_audio
        """
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "preview_text": preview_text,
            "aigc_watermark": aigc_watermark,
        }

        if voice_id:
            payload["voice_id"] = voice_id

        response = requests.post(
            f"{self.BASE_URL}/v1/voice_design",
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

        return {
            "voice_id": result.get("voice_id"),
            "trial_audio": result.get("trial_audio"),
        }

    def save_trial_audio(
        self,
        result: Dict[str, Any],
        filename: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Save trial audio

        Args:
            result: Result from design_voice
            filename: Filename (without path), default uses trial_{voice_id}.mp3
            output_dir: Output directory, default ./assets/audios

        Returns:
            Full path of saved file
        """
        trial_audio_hex = result.get("trial_audio")
        if not trial_audio_hex:
            raise ValueError("No trial audio in result")

        # Determine output directory
        if output_dir is None:
            output_dir = _get_default_output_dir()
        else:
            output_dir = Path(output_dir)

        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if filename is None:
            voice_id = result.get("voice_id", "unknown")
            filename = f"trial_{voice_id}.mp3"

        output_path = output_dir / filename

        audio_bytes = bytes.fromhex(trial_audio_hex)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        print(f"Trial audio saved to: {output_path}")
        return str(output_path)


class APIError(Exception):
    """API Error Exception"""
    pass


def main():
    """Command-line usage example"""
    import argparse

    parser = argparse.ArgumentParser(description="MiniMax Voice Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # list voices
    list_parser = subparsers.add_parser("list", help="List voices")
    list_parser.add_argument("--type", default="all", help="Voice type")

    # clone voice
    clone_parser = subparsers.add_parser("clone", help="Clone voice")
    clone_parser.add_argument("--file", required=True, help="Audio file path")
    clone_parser.add_argument("--voice-id", required=True, help="Voice ID")
    clone_parser.add_argument("--text", help="Preview text")
    clone_parser.add_argument("--model", default="speech-2.8-hd", help="Model")

    # design voice
    design_parser = subparsers.add_parser("design", help="Design voice")
    design_parser.add_argument("--prompt", required=True, help="Voice description")
    design_parser.add_argument("--preview", required=True, help="Preview text")
    design_parser.add_argument("--output", default="trial.mp3", help="Output file")

    args = parser.parse_args()

    manager = MiniMaxVoiceManager()

    if args.command == "list":
        voices = manager.list_voices(args.type)
        for category, voice_list in voices.items():
            if voice_list:
                print(f"\n{category.upper()}:")
                for v in voice_list:
                    print(f"  - {v.get('voice_id')}: {v.get('voice_name', 'N/A')}")

    elif args.command == "clone":
        print("Uploading file...")
        upload = manager.upload_voice_clone_file(args.file)
        print(f"File uploaded: {upload['file_id']}")

        print("Cloning voice...")
        result = manager.clone_voice(
            file_id=upload["file_id"],
            voice_id=args.voice_id,
            text=args.text,
            model=args.model if args.text else None
        )
        print(f"Voice cloned: {result['voice_id']}")
        if result.get("demo_audio"):
            print(f"Demo audio: {result['demo_audio']}")

    elif args.command == "design":
        print("Designing voice...")
        result = manager.design_voice(
            prompt=args.prompt,
            preview_text=args.preview
        )
        print(f"Voice designed: {result['voice_id']}")
        manager.save_trial_audio(result, args.output)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
