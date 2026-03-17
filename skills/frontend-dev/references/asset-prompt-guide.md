# Prompt Engineering Guide

## Image Prompts

- Be specific about composition: "left-aligned subject with negative space on the right for text overlay"
- Specify lighting: "soft studio lighting", "golden hour backlight", "flat diffused light"
- Include style modifiers: "editorial photography", "3D render", "flat vector illustration"
- Add technical specs: "4K resolution, sharp focus, shallow depth of field"
- For web assets: always mention "clean background", "web-optimized", "high contrast for readability"
- **NEVER** include text in image prompts unless explicitly requested — AI text rendering is unreliable

## Video Prompts

- Use MiniMax camera commands in brackets: `[Push in]`, `[Truck left]`, `[Tracking shot]`, etc.
- Describe scene, subject, lighting, and mood — the API auto-optimizes prompts by default
- For web backgrounds: keep 6s duration, add `[Static shot]` for stability
- Max 2,000 characters

## Audio / TTS

- Specify genre, tempo (BPM), mood, and instruments
- For background music: "no vocals, suitable for background, not distracting"
- For sound effects: be extremely specific about the sound event
- For TTS: choose voice matching content language and speaker gender

## Preset Shortcuts

| Shortcut | Spec |
|----------|------|
| `hero` | 16:9 (1280x720) image, cinematic, text-safe space |
| `thumb` | 1:1 (1024x1024) image, centered subject |
| `icon` | 1:1 (1024x1024), flat style, clean background |
| `avatar` | 1:1 (1024x1024), portrait, circular crop ready |
| `banner` | 21:9 (1344x576), OG/social banner |
| `portrait` | 2:3 (832x1248), vertical portrait |
| `mobile` | 9:16 (720x1280), mobile fullscreen |
| `bg-video` | 768P, 6s, `[Static shot]`, MiniMax Hailuo-2.3 |
| `video` | 768P, 6s, MiniMax Hailuo-2.3, prompt auto-optimized |
| `video-hd` | 1080P, 6s, MiniMax Hailuo-2.3 |
| `bgm` | 30s background music, no vocals, loopable |
| `sfx` | Short sound effect, < 3s |
| `tts` | Text-to-speech, MiniMax HD, MP3 |
| `narration` | Expressive narration voice, MiniMax |
