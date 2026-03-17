# Installing MiniMax Skills for OpenCode

## Prerequisites

- [OpenCode.ai](https://opencode.ai) installed

## Installation

Add minimax-skills to the `plugin` array in your `opencode.json` (global or project-level):

```json
{
  "plugin": ["minimax-skills@git+https://github.com/MiniMax-AI/skills.git"]
}
```

Restart OpenCode. That's it — the plugin auto-installs and registers all skills.

Verify by asking: "List available skills"

## Available Skills

- **frontend-dev** — Frontend development with UI design, animations, AI-generated media assets
- **fullstack-dev** — Full-stack backend architecture and frontend-backend integration
- **android-native-dev** — Android native application development with Material Design 3

## Usage

Use OpenCode's native `skill` tool:

```
use skill tool to list skills
use skill tool to load minimax-skills/frontend-dev
```

## Updating

MiniMax Skills updates automatically when you restart OpenCode.

To pin a specific version:

```json
{
  "plugin": ["minimax-skills@git+https://github.com/MiniMax-AI/skills.git#v1.0.0"]
}
```

## Troubleshooting

### Plugin not loading

1. Check logs: `opencode run --print-logs "hello" 2>&1 | grep -i minimax`
2. Verify the plugin line in your `opencode.json`
3. Make sure you're running a recent version of OpenCode

### Skills not found

1. Use `skill` tool to list what's discovered
2. Check that the plugin is loading (see above)

### Tool mapping

When skills reference Claude Code tools:
- `TodoWrite` → `todowrite`
- `Task` with subagents → `@mention` syntax
- `Skill` tool → OpenCode's native `skill` tool
- File operations → your native tools

## Getting Help

- Report issues: https://github.com/MiniMax-AI/skills/issues
