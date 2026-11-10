#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
MiniMax-H3-Image — text-to-image and image editing.

Usage:
  python minimax_image.py "A cat in space" -o cat.png
  python minimax_image.py "Mountain landscape" -o bg.png --ratio 16:9 --area 1K
  python minimax_image.py "Product icons" -o icons.png -n 4 --ratio 1:1
  python minimax_image.py "Put the hat on the person" -o out.png --image person.jpg --image hat.png

Env: MINIMAX_API_KEY (required)
"""

import os
import sys
import argparse
import base64
import mimetypes
import requests

API_KEY = os.getenv("MINIMAX_API_KEY")
# China Mainland: https://api.minimaxi.com/v1
# Overseas:       https://api.minimax.io/v1
API_BASE = os.getenv("MINIMAX_API_BASE")
if not API_BASE:
    raise SystemExit("ERROR: MINIMAX_API_BASE is not set.")

MODEL = "MiniMax-H3-Image"
TIMEOUT = 600


def _headers():
    if not API_KEY:
        raise SystemExit("ERROR: MINIMAX_API_KEY is not set.\n  export MINIMAX_API_KEY='your-key'")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def _mime(raw: bytes, path: str) -> str:
    if raw.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if raw.startswith(b"\x89PNG"):
        return "image/png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    mime, _ = mimetypes.guess_type(path)
    return mime or "image/png"


def _output_format(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".png":
        return "png"
    if ext == ".webp":
        return "webp"
    return "jpg"


def _to_image_url(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://", "data:")):
        return path_or_url
    with open(path_or_url, "rb") as f:
        raw = f.read()
    mime = _mime(raw, path_or_url)
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def generate_image(
    prompt: str,
    aspect_ratio: str = None,
    area: str = None,
    size: str = None,
    n: int = 1,
    response_format: str = "url",
    output_format: str = None,
    images: list = None,
) -> dict:
    """Generate or edit image(s). Returns API response dict."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "n": n,
        "response_format": response_format,
    }
    if output_format:
        payload["output_format"] = output_format
    if size:
        payload["size"] = size
    else:
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if area:
            payload["area"] = area

    if images:
        payload["images"] = [{"image_url": _to_image_url(img)} for img in images]
        endpoint = f"{API_BASE}/images/edits"
    else:
        endpoint = f"{API_BASE}/images/generations"

    resp = requests.post(endpoint, headers=_headers(), json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    err = data.get("error")
    if err:
        if isinstance(err, dict):
            raise SystemExit(f"API Error: {err.get('message', err)}")
        raise SystemExit(f"API Error: {err}")
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


def _items(result: dict) -> list:
    data = result.get("data")
    if not isinstance(data, list) or not data:
        raise SystemExit("API Error: no image in response")
    return data


def _numbered_path(path: str, index: int) -> str:
    """Insert index before extension: out.png -> out-0.png"""
    base, ext = os.path.splitext(path)
    return f"{base}-{index}{ext}"


def main():
    p = argparse.ArgumentParser(description="MiniMax-H3-Image text-to-image and image editing")
    p.add_argument("prompt", help="Image description")
    p.add_argument("-o", "--output", required=True, help="Output file path (.png/.jpg)")
    p.add_argument("--ratio", default=None, help="Aspect ratio, e.g. 1:1, 16:9")
    p.add_argument("--area", default=None, choices=["1K", "2K", "4K"], help="Area level 1K/2K/4K (default: 4K)")
    p.add_argument("--size", default=None, help="Exact size WxH, e.g. 1024x1024 (not with --ratio/--area)")
    p.add_argument("--image", action="append", default=None, help="Reference image path or URL (repeatable, 1-16)")
    p.add_argument("-n", "--count", type=int, default=1, help="Number of images (1-10, default: 1)")
    p.add_argument("--base64", action="store_true", help="Use b64_json response instead of URL")
    args = p.parse_args()

    if args.size and (args.ratio or args.area):
        raise SystemExit("ERROR: --size cannot be combined with --ratio or --area")
    if args.count < 1 or args.count > 10:
        raise SystemExit("ERROR: -n must be between 1 and 10")
    if args.image and len(args.image) > 16:
        raise SystemExit("ERROR: --image accepts at most 16 references")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    fmt = "b64_json" if args.base64 else "url"
    result = generate_image(
        prompt=args.prompt,
        aspect_ratio=args.ratio,
        area=args.area,
        size=args.size,
        n=args.count,
        response_format=fmt,
        output_format=_output_format(args.output),
        images=args.image,
    )

    items = _items(result)
    for i, item in enumerate(items):
        path = args.output if len(items) == 1 else _numbered_path(args.output, i)
        if args.base64:
            b64 = item.get("b64_json")
            if not b64:
                raise SystemExit("API Error: no image in response")
            raw = base64.b64decode(b64)
            with open(path, "wb") as f:
                f.write(raw)
            print(f"OK: {len(raw)} bytes -> {path}")
        else:
            url = item.get("url")
            if not url:
                raise SystemExit("API Error: no image in response")
            size = download_and_save(url, path)
            print(f"OK: {size} bytes -> {path}")


if __name__ == "__main__":
    main()
