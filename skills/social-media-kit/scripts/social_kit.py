#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Social Media Kit — batch image generator with platform presets.

Usage:
  python social_kit.py --brand "Acme" --prompt "modern tech product" --platforms instagram_post x_post -o output/
  python social_kit.py --brand "Cafe" --prompt "cozy coffee shop" --platforms all -o output/

Env: MINIMAX_API_KEY (required)
"""

import argparse
import os
import subprocess
import sys

PLATFORMS = {
    "instagram_post": {"ratio": "1:1", "label": "Instagram Post", "style": "centered composition, clean and polished, social media post, square format"},
    "instagram_story": {"ratio": "9:16", "label": "Instagram Story", "style": "vertical composition, full-height layout, mobile-first design"},
    "x_post": {"ratio": "16:9", "label": "X/Twitter Post", "style": "wide horizontal composition, clean background, room for text overlay"},
    "youtube_thumb": {"ratio": "16:9", "label": "YouTube Thumbnail", "style": "bold and eye-catching, high contrast, dramatic lighting, thumbnail style"},
    "linkedin_post": {"ratio": "16:9", "label": "LinkedIn Post", "style": "professional and clean, corporate-friendly, modern business aesthetic"},
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_SCRIPT = os.path.join(SCRIPT_DIR, "minimax_image.py")


def generate_for_platform(brand: str, prompt: str, platform: str, output_dir: str) -> str:
    """Generate an image for a specific platform. Returns output path."""
    spec = PLATFORMS[platform]
    full_prompt = f"{prompt}, {spec['style']}"
    filename = f"{brand.lower().replace(' ', '_')}_{platform}.png"
    output_path = os.path.join(output_dir, filename)

    cmd = [
        sys.executable, IMAGE_SCRIPT,
        full_prompt,
        "-o", output_path,
        "--ratio", spec["ratio"],
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR [{platform}]: {result.stderr.strip()}", file=sys.stderr)
        return ""

    print(f"OK [{spec['label']}]: {output_path}")
    return output_path


def main():
    p = argparse.ArgumentParser(description="Social Media Kit — batch image generator")
    p.add_argument("--brand", required=True, help="Brand or product name")
    p.add_argument("--prompt", required=True, help="Content description (visual style, theme)")
    p.add_argument("--platforms", nargs="+", default=["all"],
                   choices=list(PLATFORMS.keys()) + ["all"],
                   help="Platforms to generate for (default: all)")
    p.add_argument("-o", "--output-dir", required=True, help="Output directory")
    args = p.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if not os.path.exists(IMAGE_SCRIPT):
        raise SystemExit(f"ERROR: minimax_image.py not found at {IMAGE_SCRIPT}")

    platforms = list(PLATFORMS.keys()) if "all" in args.platforms else args.platforms

    print(f"Generating {len(platforms)} images for \"{args.brand}\"...\n")

    results = []
    for platform in platforms:
        path = generate_for_platform(args.brand, args.prompt, platform, args.output_dir)
        if path:
            results.append((platform, path))

    print(f"\nDone: {len(results)}/{len(platforms)} images generated")
    for platform, path in results:
        spec = PLATFORMS[platform]
        print(f"  {spec['label']:25s} ({spec['ratio']}): {path}")


if __name__ == "__main__":
    main()
