#!/usr/bin/env python3
"""
MiniMax Long Text Text-to-Speech (Async) API Client
Supports creating async tasks and querying task status
API: POST /v1/t2a_async_v2, GET /v1/query/t2a_async_query_v2
"""

import os
import time
import tarfile
import io
import requests
from typing import Optional, Dict, Any, Union
from pathlib import Path


def _get_default_output_dir() -> Path:
    """Get default audio output directory"""
    return Path.cwd() / "assets" / "audios"


class MiniMaxAsyncTTS:
    """MiniMax Async Text-to-Speech Client"""

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

    # Supported emotions
    EMOTIONS = [
        "happy", "sad", "angry", "fearful",
        "disgusted", "surprised", "calm", "fluent", "whisper"
    ]

    def __init__(self, api_key: Optional[str] = None, group_id: Optional[str] = None):
        """
        Initialize async TTS client

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
                "Or pass api_key parameter to MiniMaxAsyncTTS()."
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

    def create_task(
        self,
        text: Optional[str] = None,
        text_file_id: Optional[int] = None,
        voice_id: str = "",
        model: str = "speech-2.8-hd",
        speed: float = 1.0,
        vol: float = 1.0,
        pitch: int = 0,
        emotion: Optional[str] = None,
        sample_rate: int = 32000,
        bitrate: int = 128000,
        format: str = "mp3",
        channel: int = 2,
        pronunciation_dict: Optional[Dict] = None,
        language_boost: Optional[str] = None,
        voice_modify: Optional[Dict] = None,
        continuous_sound: bool = False,
        aigc_watermark: bool = False,
    ) -> Dict[str, Any]:
        """
        Create async text-to-speech task

        Args:
            text: Text to synthesize, length limit < 50000 characters, exclusive with text_file_id
            text_file_id: Text file ID, exclusive with text
            voice_id: Voice ID (required)
            model: Model version
            speed: Speech speed [0.5, 2]
            vol: Volume (0, 10]
            pitch: Pitch [-12, 12]
            emotion: Emotion
            sample_rate: Sample rate
            bitrate: Bitrate
            format: Audio format
            channel: Channel count
            pronunciation_dict: Pronunciation dictionary
            language_boost: Language boost
            voice_modify: Voice effects
            continuous_sound: Continuous sound optimization
            aigc_watermark: Add watermark

        Returns:
            Dictionary containing task_id, file_id, task_token
        """
        if not text and not text_file_id:
            raise ValueError("Either text or text_file_id must be provided")

        if text and len(text) > 50000:
            raise ValueError("Text length must be < 50000 characters")

        if not voice_id:
            raise ValueError("voice_id is required")

        if model not in self.MODELS:
            raise ValueError(f"Unsupported model: {model}")

        payload: Dict[str, Any] = {
            "model": model,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": speed,
                "vol": vol,
                "pitch": pitch,
            },
            "audio_setting": {
                "audio_sample_rate": sample_rate,
                "bitrate": bitrate,
                "format": format,
                "channel": channel,
            },
            "continuous_sound": continuous_sound,
            "aigc_watermark": aigc_watermark,
        }

        if text:
            payload["text"] = text
        elif text_file_id:
            payload["text_file_id"] = text_file_id

        if emotion and emotion in self.EMOTIONS:
            payload["voice_setting"]["emotion"] = emotion

        if pronunciation_dict:
            payload["pronunciation_dict"] = pronunciation_dict

        if language_boost:
            payload["language_boost"] = language_boost

        if voice_modify:
            payload["voice_modify"] = voice_modify

        response = requests.post(
            f"{self.BASE_URL}/v1/t2a_async_v2",
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
            "task_id": result.get("task_id"),
            "file_id": result.get("file_id"),
            "task_token": result.get("task_token"),
            "usage_characters": result.get("usage_characters"),
        }

    def query_task(self, task_id: Union[str, int]) -> Dict[str, Any]:
        """
        Query async task status

        Args:
            task_id: Task ID

        Returns:
            Task status information, includes status, file_id, etc.
        """
        response = requests.get(
            f"{self.BASE_URL}/v1/query/t2a_async_query_v2",
            headers=self._get_headers(),
            params={"task_id": str(task_id)}
        )
        response.raise_for_status()

        result = response.json()

        if result.get("base_resp", {}).get("status_code") != 0:
            raise APIError(
                f"API Error: {result['base_resp']['status_msg']} "
                f"(code: {result['base_resp']['status_code']})"
            )

        return {
            "task_id": result.get("task_id"),
            "status": result.get("status"),
            "file_id": result.get("file_id"),
        }

    def wait_for_completion(
        self,
        task_id: Union[str, int],
        poll_interval: float = 5.0,
        timeout: float = 600.0
    ) -> Dict[str, Any]:
        """
        Wait for task completion

        Args:
            task_id: Task ID
            poll_interval: Polling interval (seconds), default 5 seconds
            timeout: Timeout (seconds), default 600 seconds

        Returns:
            Task result

        Raises:
            TimeoutError: Timeout not completed
            APIError: Task failed
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.query_task(task_id)
            status = result.get("status", "").lower()

            if status == "success":
                return result
            elif status == "failed":
                raise APIError(f"Task {task_id} failed")
            elif status == "expired":
                raise APIError(f"Task {task_id} expired")

            time.sleep(poll_interval)

        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")

    def download_result(
        self,
        file_id: Union[str, int],
        filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        file_type: str = "audio"
    ) -> str:
        """
        Download task result file

        Args:
            file_id: File ID
            filename: Filename (without path), default uses tts_async_{file_id}.{ext}
            output_dir: Output directory, default ./assets/audios
            file_type: File type (audio/subtitle/extra_info)

        Returns:
            Full path of saved file
        """
        # Determine output directory
        if output_dir is None:
            output_dir = _get_default_output_dir()
        else:
            output_dir = Path(output_dir)

        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if filename is None:
            ext = "mp3" if file_type == "audio" else file_type
            filename = f"tts_async_{file_id}.{ext}"

        output_path = output_dir / filename

        # Step 1: Get file metadata and download URL
        response = requests.get(
            f"{self.BASE_URL}/v1/files/retrieve",
            headers=self._get_headers(),
            params={"file_id": str(file_id), "type": file_type}
        )
        response.raise_for_status()

        result = response.json()

        if result.get("base_resp", {}).get("status_code") != 0:
            raise APIError(
                f"API Error: {result['base_resp']['status_msg']} "
                f"(code: {result['base_resp']['status_code']})"
            )

        # Extract download URL
        download_url = result.get("file", {}).get("download_url")
        if not download_url:
            raise APIError(f"No download URL in response for file_id: {file_id}")

        # Step 2: Get actual file content from download URL
        audio_response = requests.get(download_url, timeout=120)
        audio_response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(audio_response.content)

        file_size = len(audio_response.content)
        print(f"File downloaded to: {output_path}")
        print(f"  Size: {file_size} bytes")
        return str(output_path)


class APIError(Exception):
    """API Error Exception"""
    pass


def main():
    """Command-line usage example"""
    import argparse

    parser = argparse.ArgumentParser(description="MiniMax Async Text-to-Speech")
    parser.add_argument("--text", "-t", required=True, help="Text to synthesize")
    parser.add_argument("--voice", "-v", required=True, help="Voice ID")
    parser.add_argument("--model", "-m", default="speech-2.8-hd", help="Model name")
    parser.add_argument("--output", "-o", default="output.mp3", help="Output file")
    parser.add_argument("--wait", "-w", action="store_true", help="Wait for completion")

    args = parser.parse_args()

    client = MiniMaxAsyncTTS()

    # Create task
    print("Creating async task...")
    task = client.create_task(
        text=args.text,
        voice_id=args.voice,
        model=args.model
    )
    print(f"Task created: {task['task_id']}")

    if args.wait:
        print("Waiting for completion...")
        result = client.wait_for_completion(task["task_id"])
        print(f"Task completed! File ID: {result['file_id']}")
        client.download_result(result["file_id"], args.output)


if __name__ == "__main__":
    main()
