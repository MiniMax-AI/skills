---
name: skill-hygiene
description: |
  Detect and repair broken SKILL.md files used by MiniMax Code and other
  MiniMax plugin hosts, plus work around a known in-memory cache bug in
  the desktop daemon (`mavis skill show` returns an empty description
  for skills that were originally scanned without valid YAML frontmatter).
  Use when: (a) `mavis skill ls` lists a skill with an empty description,
  (b) `mavis skill show <name>` returns `"description": ""` even though
  the file on disk has a clean `--- name/description ---` block,
  (c) the agent tool fails to load a skill that is present on disk, or
  (d) auditing a skills folder before publishing a new skill collection.
license: MIT
metadata:
  version: "1.0.0"
  category: meta
  audience: skill-authors, contributors, ops
  sources:
    - MiniMax Code desktop daemon (com.minimax.agent) — bundle reverse engineering during
      smoke test on 2026-07-04 (MiniMax Team, San Francisco).
    - Gray-matter / YAML frontmatter convention used by Anthropic's
      claude-code skill plugins and adopted by MiniMax plugins.
---

# Skill Hygiene

MiniMax Code, OpenCode, Cursor, Claude Code and Codex all read agent
skills from a flat directory of `SKILL.md` files. When those files
break the YAML-frontmatter contract, three failure modes appear:

1. The boot-time indexer skips the skill entirely. `mavis skill ls`
   then shows the skill with an empty `description` (or omits it from
   `/api/agent/:name/skill`).
2. `mavis skill show <name>` returns a stale empty response because
   the daemon keeps an in-memory copy that pre-dates the on-disk fix
   (`packages/skill/dist/skill.js` — `this.skillIndex.get(...)`
   fallback chain at line 80). The on-disk SKILL.md is correct, but
   the daemon will not refresh it until you restart the desktop
   client or push an explicit `mavis skill update`.
3. The agent tool cannot load the skill because `available_skills`
   were never injected into the system prompt at boot.

This skill gives you a one-shot scanner + repair script for case 1
and the exact commands to recover from cases 2 and 3 without
restarting the whole desktop app.

## When to invoke

Trigger this skill the moment you see any of:

```
$ mavis skill ls mavis | jq '.skills[] | select(.description == "")'
"secure-by-design-review"
```

```
$ mavis skill show secure-by-design-review | jq .description
""
```

```
$ claude /skill secure-by-design-review
skill_not_found
```

Do **not** invoke it for routine content edits — frontmatter is the
only thing this skill touches.

## Quick start

```bash
# 1. Audit (read-only) — see which SKILL.md files are missing or have
#    invalid YAML frontmatter.
python3 scripts/fix-skill-frontmatter.py --dry \
    --skills-dir ~/.minimax/skills
python3 scripts/fix-skill-frontmatter.py --dry \
    --skills-dir ~/.minimax/agents/mavis/skills

# 2. Apply the fix in place (atomic write per file).
SKILLS_DIR=~/.minimax/skills           python3 scripts/fix-skill-frontmatter.py
SKILLS_DIR=~/.minimax/agents/mavis/skills python3 scripts/fix-skill-frontmatter.py

# 3. Re-scan with the daemon. Use `mavis skill update --file <path>`
#    for each repair so the in-memory `skillIndex` catches up
#    *without* a desktop restart.
mavis skill update secure-by-design-review \
    -a mavis \
    --file ~/.minimax/skills/secure-by-design-review/SKILL.md
```

The script recognises two frontmatter shapes used in the wild and
repairs both. It only modifies files that genuinely need fixing, and
it never touches the body content below the frontmatter.

## Recognised shapes

**Shape A — correct frontmatter** (left alone):

```markdown
---
name: example
description: One-line summary that includes trigger conditions.
---

# Example skill
…
```

**Shape B — legacy human-readable header** (repaired):

```markdown
# Skill: Example

name: example
description: One-line summary that includes trigger conditions.

## Workflow
…
```

Shape B is what the MiniMax desktop daemon emits when a skill is
installed from a marketplace bundle where the original author skipped
the YAML block. The daemon silently indexes it with `description=""`
and the entry then disappears from `mavis skill ls` after the first
crash or restart.

## Repair algorithm

The script is intentionally trivial so it is auditable in one read:

1. Read the first 5 lines.
2. If line 1 starts with `---`, treat the file as already valid.
3. Else, if line 1 starts with `# Skill:`, extract `name:` and
   `description:` from lines 1–5, prepend a fresh frontmatter block,
   drop the duplicate `name:` / `description:` lines, and atomically
   rewrite the file.
4. Else, abort with a clear "unknown shape" error and **do not**
   touch the file.

No diffs, no merges, no opt-in flags beyond `--dry`.

## Cache recovery (case 2)

`mavis skill show` reads from an in-memory `skillIndex` that hydrates
once at daemon boot from `~/.minimax/sqlite.db`. Even after a clean
on-disk repair, the daemon will keep returning the stale empty
description until you kick the index. Two recovery paths:

```bash
# Path A — preferred. Re-publish the file through the CLI so the
#           daemon re-runs the file-watcher upsert path.
mavis skill update <skill-name> -a mavis \
    --file <absolute-path-to-SKILL.md>

# Path B — last resort. Force the desktop app to restart.
launchctl kickstart -k gui/$(id -u)/com.mavis.daemon
```

`launchctl kickstart` is a sledgehammer — it tears down a live
daemon and can produce `MODULE_NOT_FOUND` noise in
`~/.minimax/logs/launchd-stderr.log` if it cannot resolve
`better-sqlite3` (set `MAVIS_SQLITE3_MODULE_PATH` to
`/Applications/MiniMax Code.app/Contents/Resources/app.asar.unpacked`
to force the right `node_modules` lookup). Path A avoids all of that.

## Files

| Path | Purpose |
|------|---------|
| `scripts/fix-skill-frontmatter.py` | Audit + repair script (pure stdlib). |
| `references/daemon-cache-workaround.md` | Deep dive on the cache bug and the recovery paths. |

## Limits

- The script only repairs SKILL.md files whose first line is `# Skill:`.
  Files with a different preamble are reported and left untouched —
  the goal is to be boring and reviewable, not magical.
- The repair is a structural rewrite — it does not retry every front
  edge case (anchor names, multi-line scalars, escaping). If you
  author skills with exotic YAML, validate them yourself.
- The cache-recovery instructions target `MiniMax Code.app` on macOS.
  Adjust the `launchctl` label for the local platform.
