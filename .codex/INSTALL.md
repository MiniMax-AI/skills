# Installing MiniMax Skills for Codex

Enable MiniMax skills in Codex via native skill discovery. Just clone and symlink.

## Prerequisites

- Git

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MiniMax-AI/skills.git ~/.codex/minimax-skills
   ```

2. **Create the skills symlink:**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/minimax-skills/skills ~/.agents/skills/minimax-skills
   ```

   **Windows (PowerShell):**
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\minimax-skills" "$env:USERPROFILE\.codex\minimax-skills\skills"
   ```

3. **Restart Codex** (quit and relaunch the CLI) to discover the skills.

## Available Skills

- **frontend-dev** — Frontend development with UI design, animations, AI-generated media assets
- **fullstack-dev** — Full-stack backend architecture and frontend-backend integration
- **android-native-dev** — Android native application development with Material Design 3
- **ios-application-dev** — iOS application development with UIKit, SnapKit, and SwiftUI
- **shader-dev** — GLSL shader techniques for stunning visual effects (ShaderToy-compatible)

## Verify

```bash
ls -la ~/.agents/skills/minimax-skills
```

You should see a symlink (or junction on Windows) pointing to your minimax-skills skills directory.

## Updating

```bash
cd ~/.codex/minimax-skills && git pull
```

Skills update instantly through the symlink.

## Uninstalling

```bash
rm ~/.agents/skills/minimax-skills
```

Optionally delete the clone: `rm -rf ~/.codex/minimax-skills`.
