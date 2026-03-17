#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Batch MP4 → GIF converter using ffmpeg.

Usage:
  python convert_mp4_to_gif.py sticker_hi.mp4 sticker_laugh.mp4 sticker_cry.mp4 sticker_love.mp4
  python convert_mp4_to_gif.py *.mp4 --fps 12 --width 320
  python convert_mp4_to_gif.py input.mp4 -o custom_output.gif

Requires: ffmpeg (must be on PATH)
"""

import os
import sys
import argparse
import subprocess
import shutil


def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        raise SystemExit("ERROR: ffmpeg not found. Install via: brew install ffmpeg / apt install ffmpeg")


def mp4_to_gif(input_path: str, output_path: str, fps: int = 15, width: int = 360):
    """Convert a single MP4 to GIF via ffmpeg two-pass (palette for quality)."""
    if not os.path.isfile(input_path):
        print(f"SKIP: {input_path} not found", file=sys.stderr)
        return False

    palette = output_path + ".palette.png"
    scale_filter = f"fps={fps},scale={width}:-1:flags=lanczos"

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path,
             "-vf", f"{scale_filter},palettegen=stats_mode=diff",
             palette],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-i", palette,
             "-lavfi", f"{scale_filter} [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
             output_path],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"FAIL: {input_path} -> {e.stderr.decode()[-200:]}", file=sys.stderr)
        return False
    finally:
        if os.path.exists(palette):
            os.remove(palette)

    size = os.path.getsize(output_path)
    print(f"OK: {size:,} bytes -> {output_path}")
    return True


def main():
    p = argparse.ArgumentParser(description="Batch MP4 → GIF converter (ffmpeg two-pass palette)")
    p.add_argument("inputs", nargs="+", help="MP4 file(s) to convert")
    p.add_argument("-o", "--output", default=None, help="Output path (only for single file input)")
    p.add_argument("--fps", type=int, default=15, help="GIF frame rate (default: 15)")
    p.add_argument("--width", type=int, default=360, help="GIF width in pixels, height auto-scaled (default: 360)")
    args = p.parse_args()

    if args.output and len(args.inputs) > 1:
        raise SystemExit("ERROR: -o/--output only works with a single input file")

    check_ffmpeg()

    ok, fail = 0, 0
    for mp4 in args.inputs:
        if args.output:
            gif_path = args.output
        else:
            gif_path = os.path.splitext(mp4)[0] + ".gif"

        if mp4_to_gif(mp4, gif_path, fps=args.fps, width=args.width):
            ok += 1
        else:
            fail += 1

    print(f"\nDone: {ok} converted, {fail} failed")


if __name__ == "__main__":
    main()
