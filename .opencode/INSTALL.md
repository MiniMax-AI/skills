# Installing MiniMax Skills for OpenCode

## Prerequisites

- [OpenCode.ai](https://opencode.ai) installed

## Installation

### macOS / Linux

```bash
git clone https://github.com/MiniMax-AI/skills.git ~/.minimax-skills

mkdir -p ~/.config/opencode/skills
ln -s ~/.minimax-skills/skills/* ~/.config/opencode/skills/
```

### Windows (PowerShell)

```powershell
git clone https://github.com/MiniMax-AI/skills.git "$env:USERPROFILE\.minimax-skills"

New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\skills"
Get-ChildItem "$env:USERPROFILE\.minimax-skills\skills" -Directory | ForEach-Object {
    New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.config\opencode\skills\$($_.Name)" -Target $_.FullName
}
```

> **Note:** Creating symbolic links on Windows may require administrator privileges or Developer Mode enabled.

Restart OpenCode to discover the skills.

Verify by asking: "List available skills"

## Available Skills

- **frontend-dev** — Frontend development with UI design, animations, AI-generated media assets
- **fullstack-dev** — Full-stack backend architecture and frontend-backend integration
- **android-native-dev** — Android native application development with Material Design 3
- **ios-application-dev** — iOS application development with UIKit, SnapKit, and SwiftUI
- **shader-dev** — GLSL shader techniques for stunning visual effects (ShaderToy-compatible)

## Updating

```bash
cd ~/.minimax-skills && git pull
```

Symlinks will automatically point to the updated content — no need to re-link.

## Uninstalling

### macOS / Linux

```bash
rm -rf ~/.config/opencode/skills
rm -rf ~/.minimax-skills
```

### Windows (PowerShell)

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.config\opencode\skills"
Remove-Item -Recurse -Force "$env:USERPROFILE\.minimax-skills"
```

## Troubleshooting

### Skills not found

1. Verify symlinks exist: `ls -la ~/.config/opencode/skills/`
2. Each skill folder should contain a `SKILL.md` file
3. Restart OpenCode after installation

## Getting Help

- Report issues: https://github.com/MiniMax-AI/skills/issues
