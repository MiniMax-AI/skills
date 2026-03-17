#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
MiniMax Text-to-Video — async generation with polling and download.

Usage:
  python minimax_video.py "A cat playing piano" -o cat.mp4
  python minimax_video.py "Ocean waves [Truck left]" -o waves.mp4 --model MiniMax-Hailuo-2.3 --duration 10
  python minimax_video.py "City skyline at sunset [Push in]" -o city.mp4 --resolution 1080P

Env: MINIMAX_API_KEY (required)
"""

import os
import sys
import json
import time
import argparse
import requests

API_KEY = os.getenv("MINIMAX_API_KEY")
API_BASE = "https://api.minimax.io/v1"


def _headers():
    if not API_KEY:
        raise SystemExit("ERROR: MINIMAX_API_KEY is not set.\n  export MINIMAX_API_KEY='your-key'")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def _check_resp(data):
    base_resp = data.get("base_resp", {})
    code = base_resp.get("status_code", 0)
    if code != 0:
        msg = base_resp.get("status_msg", "Unknown error")
        raise SystemExit(f"API Error [{code}]: {msg}")


def create_task(
    prompt: str,
    model: str = "MiniMax-Hailuo-2.3",
    duration: int = 6,
    resolution: str = "768P",
    prompt_optimizer: bool = True,
) -> str:
    """Submit a video generation task. Returns task_id."""
    payload = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "prompt_optimizer": prompt_optimizer,
    }

    resp = requests.post(
        f"{API_BASE}/video_generation",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    _check_resp(data)

    task_id = data.get("task_id")
    if not task_id:
        raise SystemExit(f"No task_id in response: {json.dumps(data, indent=2)}")
    return task_id


def poll_task(task_id: str, interval: int = 10, max_wait: int = 600) -> str:
    """Poll task status until Success. Returns file_id."""
    elapsed = 0
    while elapsed < max_wait:
        resp = requests.get(
            f"{API_BASE}/query/video_generation",
            headers=_headers(),
            params={"task_id": task_id},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        _check_resp(data)

        status = data.get("status", "")
        file_id = data.get("file_id", "")

        if status == "Success":
            if not file_id:
                raise SystemExit("Task succeeded but no file_id returned")
            print(f"  Done! file_id={file_id}")
            return file_id
        elif status == "Fail":
            raise SystemExit(f"Video generation failed: {json.dumps(data, indent=2)}")
        else:
            print(f"  [{elapsed}s] Status: {status}...")
            time.sleep(interval)
            elapsed += interval

    raise SystemExit(f"Timeout after {max_wait}s. task_id={task_id}, check manually.")


def download_video(file_id: str, output_path: str):
    """Retrieve download URL via file_id and save the video."""
    resp = requests.get(
        f"{API_BASE}/files/retrieve",
        headers=_headers(),
        params={"file_id": file_id},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    _check_resp(data)

    download_url = data.get("file", {}).get("download_url", "")
    if not download_url:
        raise SystemExit(f"No download_url in response: {json.dumps(data, indent=2)}")

    print(f"  Downloading from {download_url[:80]}...")
    video_resp = requests.get(download_url, timeout=300)
    video_resp.raise_for_status()

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(video_resp.content)

    print(f"OK: {len(video_resp.content)} bytes -> {output_path}")


def generate(
    prompt: str,
    output_path: str,
    model: str = "MiniMax-Hailuo-2.3",
    duration: int = 6,
    resolution: str = "768P",
    prompt_optimizer: bool = True,
    poll_interval: int = 10,
    max_wait: int = 600,
):
    """Full pipeline: create task -> poll -> download."""
    print(f"Creating video task...")
    print(f"  Model: {model} | Duration: {duration}s | Resolution: {resolution}")
    print(f"  Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

    task_id = create_task(prompt, model, duration, resolution, prompt_optimizer)
    print(f"  task_id={task_id}")
    print(f"Waiting for generation...")

    file_id = poll_task(task_id, poll_interval, max_wait)
    download_video(file_id, output_path)


def main():
    p = argparse.ArgumentParser(description="MiniMax Text-to-Video")
    p.add_argument("prompt", help="Video description (max 2000 chars). Use [Camera Command] for camera control.")
    p.add_argument("-o", "--output", required=True, help="Output file path (.mp4)")
    p.add_argument("--model", default="MiniMax-Hailuo-2.3",
                   choices=["MiniMax-Hailuo-2.3", "MiniMax-Hailuo-02", "T2V-01-Director", "T2V-01"],
                   help="Model (default: MiniMax-Hailuo-2.3)")
    p.add_argument("--duration", type=int, default=6, choices=[6, 10], help="Duration in seconds (default: 6)")
    p.add_argument("--resolution", default="768P", choices=["720P", "768P", "1080P"], help="Resolution (default: 768P)")
    p.add_argument("--no-optimize", action="store_true", help="Disable prompt auto-optimization")
    p.add_argument("--poll-interval", type=int, default=10, help="Poll interval in seconds (default: 10)")
    p.add_argument("--max-wait", type=int, default=600, help="Max wait time in seconds (default: 600)")
    args = p.parse_args()

    generate(
        prompt=args.prompt,
        output_path=args.output,
        model=args.model,
        duration=args.duration,
        resolution=args.resolution,
        prompt_optimizer=not args.no_optimize,
        poll_interval=args.poll_interval,
        max_wait=args.max_wait,
    )


if __name__ == "__main__":
    main()
