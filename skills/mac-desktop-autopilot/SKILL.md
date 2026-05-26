---
name: mac-desktop-autopilot
description: |
  macOS local desktop automation: screenshot capture, mouse/keyboard control, and file upload to CDN for phone sharing.
  Use when: user asks to take a screenshot, capture screen, control the desktop, click a button, open an app, see what's on screen,
  or send a file from computer to phone. Trigger phrases: 截图、截屏、截个图、控制电脑、操控电脑、发文件到手机、点一下、帮我打开xxx、看看屏幕现在是什么。
  Do NOT use for: web browser automation (use Playwright MCP instead) or remote desktop (SSH/VNC).
metadata:
  version: "1.0"
  category: productivity
  license: MIT
  platform: macOS
  required_permissions:
    - Screen Recording
    - Accessibility
  dependencies:
    - pyautogui
    - screencapture (built-in macOS)
  sources:
    - macOS built-in screencapture
    - pyautogui (pip)
---

# macOS Desktop Autopilot

Local macOS desktop automation via `screencapture` (screenshot) + `pyautogui` (mouse/keyboard) + Matrix CDN (file sharing).

## Prerequisites

1. **Screen Recording permission**: System Settings → Privacy & Security → Screen Recording → authorize Terminal or MiniMax Agent
2. **Accessibility permission**: System Settings → Privacy & Security → Accessibility → authorize Terminal or MiniMax Agent
3. **pyautogui installed**: `pip3 install pyautogui --default-timeout=120`

## Procedure

### Screenshot

```bash
screencapture /tmp/screenshot.png
```

After capturing, use `describe_images` tool to read and describe the screenshot. For phone sharing, upload to CDN.

### Mouse Operations

```python
import pyautogui, time
pyautogui.FAILSAFE = True  # move to corner to abort

# Move to coordinate (pixels, origin = top-left)
pyautogui.moveTo(x, y, duration=0.3)

# Left-click
pyautogui.click(x, y)

# Double-click
pyautogui.doubleClick(x, y)

# Right-click
pyautogui.rightClick(x, y)

# Drag
pyautogui.dragTo(x2, y2, duration=0.5)

# Scroll
pyautogui.scroll(-3)  # scroll down 3 units
```

> Why FAILSAFE: moving the cursor to any screen corner triggers an emergency stop to prevent runaway automation.

### Keyboard Operations

```python
# Type text (cursor must already be in text field)
pyautogui.typewrite("Hello", interval=0.05)

# Press a key
pyautogui.press("enter")
pyautogui.press("escape")
pyautogui.press("cmd", "s")  # Cmd+S

# Combo keys
pyautogui.hotkey("cmd", "c")  # copy
pyautogui.hotkey("cmd", "v")  # paste
pyautogui.hotkey("cmd", "a")  # select all
```

### Send File to Phone

1. Upload file via `matrix_upload_to_cdn` → get CDN URL
2. Share the URL with user → download on phone

### OCR / Read Screen Content

```bash
screencapture /tmp/ocr_screen.png
```
Then analyze with `describe_images` tool to extract text.

## Output Contract

- **Screenshot**: display image directly or share CDN link
- **Mouse/keyboard**: take a confirmation screenshot immediately after action
- **File upload**: return CDN download link

## Failure Handling

| Error | Cause | Fix |
|-------|-------|-----|
| "could not create image" | Missing Screen Recording permission | User authorizes in System Settings |
| pyautogui runaway | FAILSAFE not enabled | Move cursor to screen corner to stop |
| Permission denied | Missing Accessibility permission | User authorizes in System Settings → Privacy → Accessibility |
| pyautogui not installed | pip install failed | Retry `pip3 install pyautogui --default-timeout=120` |

## Examples

**Screenshot to phone**
User: "截个图发给我"
→ `screencapture /tmp/page.png` → `matrix_upload_to_cdn(/tmp/page.png)` → return download link

**Open an app**
User: "帮我打开微信"
→ Take screenshot → OCR locate Dock → click WeChat icon

**What's on screen**
User: "现在屏幕是什么"
→ Screenshot → `describe_images` analyze → describe screen content
