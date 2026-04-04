#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
clipboard_image.py — Save image from clipboard to a temp file.
Cross-platform: macOS, Linux, Windows.

macOS: uses osascript clipboard API (TIFF then PNGf)
Linux: uses xclip or wl-paste
Windows: uses PowerShell

Usage:
    python3 clipboard_image.py [output_path]
    # If output_path omitted, saves to /tmp/vision-clipboard-<timestamp>.png

Exit codes:
    0 — image saved successfully
    1 — no image in clipboard
    2 — platform not supported / dependency missing
"""

import os
import sys
import platform
import subprocess
from datetime import datetime

TIMEOUT = 10


def save_mac_clipboard_image(output_path: str) -> bool:
    def run_osascript(script_text: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["/usr/bin/osascript", "-e", script_text],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )

    tmp_script = f"/tmp/vision_clipboard_write_{os.getpid()}.scpt"
    try:
        check_script = (
            "try\n"
            "  set img to (the clipboard as TIFF picture)\n"
            "on error\n"
            '  return "NO_TIFF"\n'
            "end try\n"
            'return "HAS_TIFF"'
        )
        r = run_osascript(check_script)
        if r.stdout.strip() != "HAS_TIFF":
            return False

        write_script = (
            "try\n"
            "  set img to (the clipboard as TIFF picture)\n"
            '  set f to open for access (POSIX file "'
            + output_path.replace('"', '\\"')
            + '") with write permission\n'
            "  try\n"
            "    write img to f\n"
            "    close access f\n"
            "  on error errMsg\n"
            "    close access f\n"
            "    error errMsg\n"
            "  end try\n"
            "on error errMsg\n"
            '  return "ERR: " & errMsg\n'
            "end try\n"
            'return "OK"'
        )

        with open(tmp_script, "w", encoding="utf-8") as f:
            f.write(write_script)

        r = subprocess.run(
            ["/usr/bin/osascript", tmp_script],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )

        if (
            r.stdout.strip() == "OK"
            and os.path.exists(output_path)
            and os.path.getsize(output_path) > 0
        ):
            return True

        return False

    finally:
        if os.path.exists(tmp_script):
            os.unlink(tmp_script)


def save_linux_clipboard_image(output_path: str) -> bool:
    for cmd in [
        ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
        ["wl-paste", "-t", "image/png"],
    ]:
        try:
            with open(output_path, "wb") as f:
                r = subprocess.run(
                    cmd, stdout=f, stderr=subprocess.DEVNULL, timeout=TIMEOUT
                )
            if (
                r.returncode == 0
                and os.path.exists(output_path)
                and os.path.getsize(output_path) > 0
            ):
                return True
        except Exception:
            continue
    return False


def save_windows_clipboard_image(output_path: str) -> bool:
    ps = (
        f"Add-Type -AssemblyName System.Windows.Forms; "
        f"$img = [System.Windows.Forms.Clipboard]::GetImage(); "
        f"if ($img) {{ $img.Save(r'{output_path}', [System.Drawing.Imaging.ImageFormat]::Png); exit 0 }} else {{ exit 1 }}"
    )
    try:
        r = subprocess.run(
            ["powershell", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
        return r.returncode == 0 and os.path.exists(output_path)
    except Exception:
        return False


def save_clipboard_image(output_path: str = None) -> str:
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/tmp/vision-clipboard-{ts}.png"

    os.makedirs(os.path.dirname(output_path) or "/tmp", exist_ok=True)

    system = platform.system()
    if system == "Darwin":
        ok = save_mac_clipboard_image(output_path)
    elif system == "Linux":
        ok = save_linux_clipboard_image(output_path)
    elif system == "Windows":
        ok = save_windows_clipboard_image(output_path)
    else:
        print(f"ERROR: Unsupported platform: {system}", file=sys.stderr)
        sys.exit(2)

    if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(output_path)
        sys.exit(0)
    else:
        print("ERROR: No image found in clipboard", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    save_clipboard_image(sys.argv[1] if len(sys.argv) > 1 else None)
