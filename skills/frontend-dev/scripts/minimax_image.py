#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
MiniMax Text-to-Image — synchronous generation.

Usage:
  python minimax_image.py "A cat in space" -o cat.png
  python minimax_image.py "Mountain landscape" -o bg.png --ratio 16:9
  python minimax_image.py "Product icons" -o icons.png -n 4 --ratio 1:1

Env: MINIMAX_API_KEY (required)
"""

import os
import sys
import json
import argparse
import requests

API_KEY = os.getenv("MINIMAX_API_KEY")
API_BASE = "https://api.minimax.io/v1"

ASPECT_RATIOS = ["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"]


def _headers():
    if not API_KEY:
        raise SystemExit("ERROR: MINIMAX_API_KEY is not set.\n  export MINIMAX_API_KEY='your-key'")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def generate_image(
    prompt: str,
    model: str = "image-01",
    aspect_ratio: str = "1:1",
    n: int = 1,
    response_format: str = "url",
    prompt_optimizer: bool = False,
    seed: int = None,
) -> dict:
    """Generate image(s). Returns API response dict."""
    payload = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "n": n,
        "response_format": response_format,
        "prompt_optimizer": prompt_optimizer,
    }
    if seed is not None:
        payload["seed"] = seed

    resp = requests.post(
        f"{API_BASE}/image_generation",
        headers=_headers(),
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        raise SystemExit(f"API Error [{base_resp.get('status_code')}]: {base_resp.get('status_msg')}")

    return data


def download_and_save(url: str, output_path: str):
    """Download image from URL and save."""
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)
    return len(resp.content)


def main():
    p = argparse.ArgumentParser(description="MiniMax Text-to-Image")
    p.add_argument("prompt", help="Image description (max 1500 chars)")
    p.add_argument("-o", "--output", required=True, help="Output file path (.png/.jpg)")
    p.add_argument("--model", default="image-01", help="Model (default: image-01)")
    p.add_argument("--ratio", default="1:1", choices=ASPECT_RATIOS, help="Aspect ratio (default: 1:1)")
    p.add_argument("-n", "--count", type=int, default=1, choices=range(1, 10), help="Number of images (1-9, default: 1)")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    p.add_argument("--optimize", action="store_true", help="Enable prompt auto-optimization")
    p.add_argument("--base64", action="store_true", help="Use base64 response instead of URL")
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    fmt = "base64" if args.base64 else "url"
    result = generate_image(
        prompt=args.prompt,
        model=args.model,
        aspect_ratio=args.ratio,
        n=args.count,
        response_format=fmt,
        prompt_optimizer=args.optimize,
        seed=args.seed,
    )

    meta = result.get("metadata", {})
    print(f"Generated: {meta.get('success_count', '?')} success, {meta.get('failed_count', '?')} failed")

    if args.base64:
        images = result.get("data", {}).get("image_base64", [])
        import base64
        for i, b64 in enumerate(images):
            path = args.output if len(images) == 1 else _numbered_path(args.output, i)
            raw = base64.b64decode(b64)
            with open(path, "wb") as f:
                f.write(raw)
            print(f"OK: {len(raw)} bytes -> {path}")
    else:
        urls = result.get("data", {}).get("image_urls", [])
        for i, url in enumerate(urls):
            path = args.output if len(urls) == 1 else _numbered_path(args.output, i)
            size = download_and_save(url, path)
            print(f"OK: {size} bytes -> {path}")


def _numbered_path(path: str, index: int) -> str:
    """Insert index before extension: out.png -> out-0.png"""
    base, ext = os.path.splitext(path)
    return f"{base}-{index}{ext}"


if __name__ == "__main__":
    main()
