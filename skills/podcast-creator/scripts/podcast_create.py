#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Podcast assembler — stitch narration + music into a final episode.

Usage:
  python podcast_create.py --intro intro.mp3 --chapters ch1.mp3 ch2.mp3 --outro outro.mp3 -o episode.mp3
  python podcast_create.py --chapters ch1.mp3 -o episode.mp3 --title "My Episode"

Requires: ffmpeg on PATH
"""

import argparse
import os
import subprocess
import sys
import tempfile


def _check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        raise SystemExit("ERROR: ffmpeg not found on PATH.\n  Install: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)")


def _get_duration(path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def _crossfade_pair(a: str, b: str, output: str, overlap: float = 2.0):
    """Crossfade two audio files with given overlap duration."""
    dur_a = _get_duration(a)
    if dur_a <= overlap:
        overlap = max(0.5, dur_a / 2)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", a,
        "-i", b,
        "-filter_complex",
        f"[0]afade=t=out:st={dur_a - overlap}:d={overlap}[a0];"
        f"[1]afade=t=in:st=0:d={overlap}[a1];"
        f"[a0][a1]acrossfade=d={overlap}:c1=tri:c2=tri",
        output,
    ], capture_output=True, check=True)


def _concat_with_silence(files: list, output: str, gap: float = 1.0):
    """Concatenate audio files with silence gaps between them."""
    if len(files) == 1:
        subprocess.run(["cp", files[0], output], check=True)
        return

    inputs = []
    filter_parts = []
    for i, f in enumerate(files):
        inputs.extend(["-i", f])
        if i < len(files) - 1:
            filter_parts.append(f"[{i}]apad=pad_dur={gap}[p{i}];")
        else:
            filter_parts.append(f"[{i}]acopy[p{i}];")

    concat_inputs = "".join(f"[p{i}]" for i in range(len(files)))
    filter_parts.append(f"{concat_inputs}concat=n={len(files)}:v=0:a=1[out]")

    subprocess.run(
        ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", "".join(filter_parts),
            "-map", "[out]",
            output,
        ],
        capture_output=True, check=True,
    )


def _set_id3(path: str, title: str = "", artist: str = ""):
    """Set basic ID3 tags on the output mp3."""
    if not title and not artist:
        return
    tmp = path + ".tagged.mp3"
    cmd = ["ffmpeg", "-y", "-i", path]
    if title:
        cmd.extend(["-metadata", f"title={title}"])
    if artist:
        cmd.extend(["-metadata", f"artist={artist}"])
    cmd.extend(["-codec", "copy", tmp])
    subprocess.run(cmd, capture_output=True, check=True)
    os.replace(tmp, path)


def main():
    p = argparse.ArgumentParser(description="Assemble podcast episode from narration + music")
    p.add_argument("--intro", default="", help="Intro music file (mp3)")
    p.add_argument("--chapters", nargs="+", required=True, help="Chapter narration files in order")
    p.add_argument("--outro", default="", help="Outro music file (mp3)")
    p.add_argument("--title", default="", help="Episode title (ID3 tag)")
    p.add_argument("--artist", default="", help="Artist/show name (ID3 tag)")
    p.add_argument("--gap", type=float, default=1.0, help="Silence between chapters in seconds (default: 1.0)")
    p.add_argument("--crossfade", type=float, default=2.0, help="Crossfade duration for intro/outro (default: 2.0)")
    p.add_argument("-o", "--output", required=True, help="Output file path")
    args = p.parse_args()

    _check_ffmpeg()

    for f in args.chapters:
        if not os.path.exists(f):
            raise SystemExit(f"ERROR: Chapter file not found: {f}")
    if args.intro and not os.path.exists(args.intro):
        raise SystemExit(f"ERROR: Intro file not found: {args.intro}")
    if args.outro and not os.path.exists(args.outro):
        raise SystemExit(f"ERROR: Outro file not found: {args.outro}")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        # Concatenate chapters with silence gaps
        chapters_combined = os.path.join(tmp, "chapters.mp3")
        _concat_with_silence(args.chapters, chapters_combined, gap=args.gap)

        current = chapters_combined

        # Crossfade intro if provided
        if args.intro:
            intro_merged = os.path.join(tmp, "with_intro.mp3")
            _crossfade_pair(args.intro, current, intro_merged, overlap=args.crossfade)
            current = intro_merged

        # Crossfade outro if provided
        if args.outro:
            final_merged = os.path.join(tmp, "with_outro.mp3")
            _crossfade_pair(current, args.outro, final_merged, overlap=args.crossfade)
            current = final_merged

        # Copy to output
        subprocess.run(["cp", current, args.output], check=True)

    # Set ID3 tags
    _set_id3(args.output, title=args.title, artist=args.artist)

    duration = _get_duration(args.output)
    size = os.path.getsize(args.output)
    mins = int(duration // 60)
    secs = int(duration % 60)

    # Print chapter timestamps
    print(f"OK: {size:,} bytes -> {args.output} (duration: {mins}m {secs:02d}s)")
    offset = 0.0
    if args.intro:
        intro_dur = _get_duration(args.intro)
        print(f"  00:00 - Intro ({intro_dur:.0f}s)")
        offset = max(0, intro_dur - args.crossfade)
    for i, ch in enumerate(args.chapters, 1):
        m, s = int(offset // 60), int(offset % 60)
        ch_dur = _get_duration(ch)
        print(f"  {m:02d}:{s:02d} - Chapter {i} ({ch_dur:.0f}s)")
        offset += ch_dur + args.gap
    if args.outro:
        m, s = int(offset // 60), int(offset % 60)
        print(f"  {m:02d}:{s:02d} - Outro")


if __name__ == "__main__":
    main()
