---
name: context-search
description: >
  Search and retrieve persistent project context across AI agent sessions.
  Load this skill when: starting a new session; encountering unfamiliar code;
  needing to understand project structure or architecture; searching for a decision
  or goal; wanting to find active files being worked on; or needing context on
  a specific file.
  Triggers: search context, find context, what's active, what files are we working on,
  look up decision, what's the architecture, show me goals, what did we do last session,
  context search, get active context.
  Also use when: you need to understand a file you haven't seen before; you want to
  check if something is stale; you want to export context to Obsidian.
license: MIT
metadata:
  version: "1.0"
  category: productivity
  tools: context-search-mcp
---

# Context Search

Search and retrieve context from `.context/` files. Works alongside `context-maintainer` — `context-search` reads what `context-maintainer` writes.

## Core Principle

**Context files are written by `context-maintainer` during work. `context-search` retrieves them.**

Never write to `.context/` files from this skill — use `context-maintainer` for that.

## Prerequisites

The `context-search-mcp` MCP server must be installed and configured.

**OpenCode** — add to `~/.config/opencode/opencode.json` or `package.json`:
```json
{
  "mcp": {
    "context-search": {
      "type": "local",
      "command": ["uvx", "context-search-mcp"],
      "enabled": true
    }
  }
}
```

Restart the app. Verify with `/mcp` — `context-search` should appear.

## MCP Tools

| Tool | When to call |
|---|---|
| `get_active_context` | New session starts — get all non-stale context |
| `search_context` | Need to find something specific in context |
| `get_file_context` | Encountering an unfamiliar file |
| `export_to_vault` | User wants to explore context in Obsidian |
| `prune_context` | User asks to clean up old stale entries |
| `check_qmd` | Check if QMD is available for semantic search |

---

## Workflows

### New Session — Jump-Start

```
1. Call get_active_context(path="/path/to/project")
   → Returns all active (non-stale) context files as readable summaries
2. Read goals.md output first — always know the goals before anything else
3. Read project.md — understand the project overview
4. Now you can work with full context of where the project is
```

### Encountering an Unfamiliar File

```
1. Call get_file_context(path="/path/to/project", filename="d2q9-bgk.c")
   → Returns: last modified, last commit, freshness, what the file does
2. Call search_context(query="d2q9-bgk.c") if you need more detail
```

### Searching for a Decision or Goal

```
1. Call search_context(query="MPI halo exchange decision")
   → Returns matching lines from decisions.md and other context files
2. If QMD is available, semantic search gives better results
```

### QMD Auto-Detection (Optional Enhancement)

On first `search_context` call, the tool checks if QMD is available:

- **QMD available + user approves:** Agent asks user: "QMD is available and enables semantic search for your context. Enable it?"
  - If yes, agent runs: `qmd collection add /path/to/.context --name project-context` + `qmd embed`
  - Subsequent `search_context` calls delegate to QMD's hybrid search
- **QMD not available:** Uses simple grep search (still works, just less semantic)

### Export to Obsidian

```
1. Call export_to_vault(context_path="/path/to/project", vault_path="/path/to/obsidian-vault")
   → Copies all .context/*.md files to the Obsidian vault
2. User can now open Obsidian and use its graph view to explore relationships
3. This is one-way (context → vault). External Obsidian changes need manual sync.
```

### Prune Old Stale Entries

```
1. Call prune_context(path="/path/to/project", older_than_days=30)
   → Removes stale entries older than 30 days
2. Present the result: "Removed X old stale entries"
```

---

## When Context-Search Triggers

**Always trigger on:**
- New session starts (`get_active_context`)
- Encountering a file you've never seen in the current session (`get_file_context`)
- User asks about architecture, goals, decisions, or project state
- Before starting a new feature, check existing context first

**Never:**
- Re-read all context files before every edit (use targeted search)
- Dump full context files into chat — summarize and be selective

---

## Context Window Efficiency

**Token-efficient pattern:**
1. `get_active_context` → returns previews (not full contents)
2. Based on previews, selectively `get_file_context` for specific files
3. `search_context` for targeted lookups

**Never load all context files fully into the chat** — use the summaries and search.

---

## Example: Starting a New Session

```
You: "continue working on the MPI benchmark"

Agent:
  1. get_active_context(path="/path/to/project")
     → goals.md: "[ACTIVE] Fix MPI halo exchange bug"
     → active-files.md: "d2q9-bgk.c, opt_log.md are HIGH freshness"
     → decisions.md: "Chose non-blocking MPI_Isend over blocking MPI_Send"
  2. Good — I know what we're doing. Resume work.
  3. Make changes
  4. update_context (via context-maintainer) when done
```

---

## Anti-Patterns

- ❌ Loading all context files fully into every response
- ❌ Writing to .context/ files from this skill (use context-maintainer)
- ❌ Searching without purpose — be targeted
- ❌ Ignoring freshness scores — HIGH freshness files deserve priority
- ❌ Forgetting to ask about goals at session start
