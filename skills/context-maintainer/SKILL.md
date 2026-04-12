---
name: context-maintainer
description: >
  Maintain persistent project context across AI agent sessions using .context/ files.
  Load this skill when: the user asks you to "understand this project" or "get context";
  you start a new session and need to understand the project; you complete significant work
  and need to record it; the user mentions goals, decisions, or architecture; or you
  encounter unfamiliar code and need context.
  Triggers: understand this project, get context, maintain context, update goals,
  record decision, log this change, what are the current goals, what's the architecture,
  what have we done so far.
  Also use when: context window is ~70% full (trigger checkpoint); you do a git commit;
  you modify more than 30 lines across files; user asks about project structure or goals.
license: MIT
metadata:
  version: "1.0"
  category: productivity
  tools: context-maintainer-mcp
---

# Context Maintainer

Maintain persistent context files in `.context/` that survive across sessions. No more re-scanning the repo every new chat.

## Core Files

`.context/` lives in the project root and contains:

| File | What it holds | When to read/write |
|---|---|---|
| `project.md` | Project overview, key files | Read at session start |
| `architecture.md` | System design, data flow | Read on demand |
| `decisions.md` | Choices made and why | Write when decision made |
| `active-files.md` | Files being worked on + freshness | Update after significant changes |
| `stale-files.md` | Deprecated approaches | Write when flagging stale |
| `goals.md` | Long-term + short-term goals | Read at start, update on checkpoint |
| `relationships.md` | Key dependencies | Read on demand |
| `recent-commits.md` | Last 10 git commits | Update after commits |

## Prerequisites

The `context-maintainer-mcp` MCP server must be installed and configured.

**OpenCode** — add to `~/.config/opencode/opencode.json` or `package.json`:
```json
{
  "mcp": {
    "context-maintainer": {
      "type": "local",
      "command": ["uvx", "context-maintainer-mcp"],
      "enabled": true
    }
  }
}
```

Restart the app. Verify with `/mcp` — `context-maintainer` should appear.

## MCP Tools

| Tool | When to call |
|---|---|
| `init_context` | User asks "understand this project" |
| `update_context` | After git commit OR significant change (>30 lines) |
| `checkpoint_goals` | Context window ~70% full OR session end |
| `flag_stale` | When a file/approach becomes outdated |
| `promote_stale` | When a stale file becomes relevant again |
| `gitignore_add` | After init_context (default: context is gitignored) |
| `gitignore_remove` | User wants to commit .context/ to repo |
| `gitignore_status` | Check if .context/ is tracked |

---

## When to Update Context

**NEVER update after every small edit.** Context updates are for significant milestones.

**Call `update_context` when:**
- After a `git add + commit` — a commit signals meaningful work is done
- You modified > 30 lines across one or more files in one session
- You add a new file that changes project structure
- You remove a significant file or feature

**Call `checkpoint_goals` when:**
- Context window is ~70% full (before it runs out)
- User says "save my progress" or ends the session
- You want to summarize what you've done before continuing

**Call `flag_stale` when:**
- A file is deprecated and replaced by a new approach
- A previous decision is invalidated by a new one
- An approach described in active-files.md is no longer relevant

---

## Workflows

### New Project — First Time

```
1. Call init_context(path="/path/to/project")
   → Creates .context/ with all files + recent commits
2. Call gitignore_add(path="/path/to/project")
   → Adds .context/ to .gitignore (context is personal by default)
3. Read goals.md — update it if user has stated goals
4. Present a brief summary of what was created
```

### New Session — Resume Work

```
1. Call get_active_context(path="/path/to/project")  [via context-search]
   OR read goals.md + project.md directly
2. Ask: "What are the current goals?" (read goals.md)
3. Continue work
4. Call update_context when significant changes happen
```

### After Significant Change (e.g., after git commit)

```
1. Call update_context(path, file="path/to/file.md", summary="What changed")
   → Updates active-files.md with freshness + git history
2. If a design decision was made, also call:
   → decisions.md entry (manually write, not via tool)
3. Call checkpoint_goals if context is getting full
```

### Before Context Runs Out (~70% window)

```
1. Call checkpoint_goals(path, short_term=["current work"], long_term=["original goals"])
   → Updates goals.md with session history
2. This frees context space — the files persist and will be read next session
```

### Recording a Decision

```
1. Read decisions.md
2. Append entry:
   ## [YYYY-MM-DD] Decision Title
   **Status:** Accepted
   **Context:** Problem or question
   **Decision:** What was chosen
   **Consequences:** What changed
```

---

## Goals.md Format

```markdown
---
last_updated: 2026-04-04T18:30:00Z
---

# Long-term Goals
- Migrate MPI halo exchange to non-blocking
- Add benchmarking suite

# Short-term Goals
- [ACTIVE] Fix MPI halo exchange bug
- [DONE] Add Change 1a timing to opt_log.md

# Session History
- [2026-04-04] Project context initialized
- [2026-04-05] Added Change 1a: MPI_Init timing
```

---

## Gitignore — Default: Excluded

`.context/` is added to `.gitignore` by default (not committed). This keeps personal context private.

**To share context with the team:**
```
Call gitignore_remove(path)  # removes .context/ from .gitignore
```
Then commit `.context/` to the repo.

**To keep context private:**
```
Call gitignore_add(path)  # re-adds .context/ to .gitignore
```

---

## Context Window Management

The agent should track its own context usage. When it notices context is ~70% full:

1. Call `checkpoint_goals` with current short-term and long-term goals
2. Summarize in-session progress into goals.md Session History
3. Continue working — next session will read goals.md and resume

**Key rule:** Never let context run out mid-task. Checkpoint proactively.

---

## Anti-Patterns

- ❌ Calling `update_context` after every file edit
- ❌ Writing full file contents into chat instead of using context files
- ❌ Ignoring goals — always know what the user is trying to achieve
- ❌ Not checkpointing before context runs out
- ❌ Committing `.context/` to git by default (personal context)
- ❌ Let stale files accumulate without flagging them
