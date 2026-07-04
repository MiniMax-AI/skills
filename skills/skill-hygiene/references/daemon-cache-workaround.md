# Daemon cache workaround — `mavis skill show` returning an empty `description`

This reference documents a reproducible interaction between
`MiniMax Code.app` (the desktop daemon, bundle id `com.mavis.daemon`,
distribution bundle `MiniMax Code.app/Contents/Resources/resources/daemon/`),
its SQLite index, and the in-memory `skillIndex` that the daemon uses
to serve `mavis skill show`. The bug was reverse-engineered from the
shipped `daemon.js` bundle during the July 2026 smoke test and the
recovery steps below are what make `secure-by-design-review` —
presently affected — visible again without restarting the whole
desktop app.

## Symptoms

```bash
$ mavis skill show secure-by-design-review | jq .description
""          # empty even though the on-disk file is correct
```

```bash
$ mavis skill ls mavis | jq '.skills[] | select(.description == "") | .name'
"a-long-list-of-fantasies"   # many skills are affected by the same bug
```

```bash
$ sqlite3 ~/.minimax/sqlite.db \
    "SELECT name, agent_name, length(description) FROM skills WHERE description='';"
# ... above may be empty for the agent `mavis` even though `show` is empty
```

## Root cause

Three things conspire:

1. The desktop daemon reads `SKILL.md` at boot to populate an
   in-memory `skillIndex`. When the YAML frontmatter block is
   missing or malformed, the indexer logs the skill as
   `description=""` and the row never gets upserted into the
   `skills` table of `~/.minimax/sqlite.db`.
2. `mavis skill show` returns what the in-memory `skillIndex` says.
   It does **not** re-parse the file from disk on every request —
   it only falls back to the file when the index entry does not
   exist (`packages/skill/dist/skill.js` — `readSkill()` method,
   the chain `meta ?? frontmatterFallback(content) ?? ""`).
3. Even when you manually `INSERT` a row into `skills`, the daemon
   does not refresh the in-memory `skillIndex` until restart. SQLite
   inserts never propagate to the running process.

The desktop bundle is not currently distributed as source, so
applying an upstream patch is not an option. The two recovery
paths below are reversible and avoid touching the desktop bundle.

## Path A — `mavis skill update` (preferred)

This is the only fix that pushes the new description through the
daemon's file-watcher upsert path without restarting the process.

```bash
# 1. Confirm the on-disk SKILL.md is correct.
head -3 ~/.minimax/skills/secure-by-design-review/SKILL.md
# ---
# name: secure-by-design-review
# description: Review and implement software with defensive security: …

# 2. Push it back through the CLI. The daemon's file watcher fires
#    the `onSkillFileChange` handler which calls
#    `this.skillIndex.upsert(skillInfo)` — at that point the
#    in-memory index agrees with the file and `show` returns the
#    real description.
mavis skill update secure-by-design-review \
    -a mavis \
    --file ~/.minimax/skills/secure-by-design-review/SKILL.md
```

If the CLI returns `50001 internal error`, the daemon failed to
parse the YAML. Double-check the file with `head` and retry. If it
returns `40400 not found`, the row does not exist in `skills` yet —
the desktop daemon skipped it at boot, which is exactly the
condition this skill exists to repair.

## Path B — kickstart (last resort)

Only useful when `mavis skill update` is unreachable (for example
when you cannot place the file in a path the daemon watches).

```bash
launchctl kickstart -k gui/$(id -u)/com.mavis.daemon
```

This tears down the daemon and asks launchd to relaunch it. Be
aware:

- The official service label is `com.mavis.daemon` (`brew services`
  equivalent). The CLI command `mavis restart` is intentionally a
  no-op on macOS because the desktop app supervises the daemon;
  the `launchctl` call below is the only way to actually cycle it.
- After kickstart, `~/.minimax/logs/launchd-stderr.log` may show
  repeated `Cannot find module 'better-sqlite3'` errors. Set
  `MAVIS_SQLITE3_MODULE_PATH` to
  `/Applications/MiniMax Code.app/Contents/Resources/app.asar.unpacked`
  before the kickstart if you want a clean boot.

## Path C — sandboxed SQLite insert (extreme)

If the desktop app is offline and you only need the agent tool to
load the skill (not the `show` CLI), an `INSERT` into
`~/.minimax/sqlite.db` is enough to make the row show up. The CLI
itself will keep returning empty until Path A is used.

```bash
python3 - <<'PY'
import sqlite3, time
db = "/Users/jordelmirsdevhome/.minimax/sqlite.db"
desc = "Review and implement software with defensive security: ..."
now = int(time.time() * 1000)
loc = "/Users/jordelmirsdevhome/.minimax/skills/secure-by-design-review/SKILL.md"
con = sqlite3.connect(db)
cur = con.cursor()
for agent_name in ("mavis", "coder", "general", "verifier"):
    cur.execute(
        """INSERT OR REPLACE INTO skills
           (name, agent_name, description, location, source_type, source_kind, created_at, updated_at)
           VALUES (?, ?, ?, ?, 2, 'user-mavis', ?, ?)""",
        ("secure-by-design-review", agent_name, desc, loc, now, now),
    )
con.commit()
PY
```

Pre-conditions:

- Backup `~/.minimax/sqlite.db` first.
- The daemon must be stopped. Use `pgrep -f daemon.js` to find the
  PID and kill it; let launchd relaunch.

## Verifying recovery

```bash
mavis skill show <name> | jq .description
# Should print the real description, not "".

mavis skill ls <agent> | jq '.skills[] | select(.name == "<name>").description'
# Same.

claude /skill <name>     # or the matching tool name in your client
# Should now load the skill instructions.
```

If `description` is still empty after Path A, the on-disk file is
probably still in Shape B (legacy human-readable header). Re-run
`scripts/fix-skill-frontmatter.py` and try Path A again.
