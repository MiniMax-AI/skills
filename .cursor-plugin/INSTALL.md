# Installing MiniMax Skills for Cursor

Enable MiniMax skills in Cursor by cloning the repository locally and pointing Cursor's skills path at the `skills/` directory.

## Prerequisites

- Cursor installed
- Git

## Installation

### macOS / Linux

```bash
git clone https://github.com/MiniMax-AI/skills.git ~/.cursor/minimax-skills
```

Set Cursor's skills path to:

```text
~/.cursor/minimax-skills/skills/
```

### Windows (PowerShell)

```powershell
git clone https://github.com/MiniMax-AI/skills.git "$env:USERPROFILE\.cursor\minimax-skills"
```

Set Cursor's skills path to:

```text
C:\Users\YOUR_USERNAME\.cursor\minimax-skills\skills\
```

Replace `YOUR_USERNAME` with your Windows account name.

After saving the path, restart Cursor or reload the window so it rescans local skills.

## Verify

Confirm the clone exists and contains `SKILL.md` files:

### macOS / Linux

```bash
find ~/.cursor/minimax-skills/skills -maxdepth 2 -name SKILL.md | head
```

### Windows (PowerShell)

```powershell
Get-ChildItem "$env:USERPROFILE\.cursor\minimax-skills\skills" -Directory | ForEach-Object {
    Get-ChildItem $_.FullName -Filter SKILL.md
}
```

## Updating

### macOS / Linux

```bash
cd ~/.cursor/minimax-skills && git pull
```

### Windows (PowerShell)

```powershell
Set-Location "$env:USERPROFILE\.cursor\minimax-skills"
git pull
```

## Uninstalling

### macOS / Linux

```bash
rm -rf ~/.cursor/minimax-skills
```

### Windows (PowerShell)

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.cursor\minimax-skills"
```

## VS Code Note

This repository does not currently ship a standalone VS Code extension.

If you use VS Code, the recommended options are:
- run a supported CLI tool such as Codex, Claude Code, or OpenCode inside the VS Code integrated terminal
- use Cursor if you want native local-skills configuration from this repository
