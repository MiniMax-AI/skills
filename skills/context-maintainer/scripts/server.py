#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
context-maintainer MCP server — manages .context/ files for AI coding agents.

Usage:
    uvx context-maintainer-mcp

Provides tools for creating, updating, and managing project context files
that persist across AI agent sessions.

Environment:
    No external dependencies — Python stdlib only.
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime, timezone

CONTEXT_DIR = ".context"
CTX_FILES = [
    "project.md",
    "architecture.md",
    "decisions.md",
    "active-files.md",
    "stale-files.md",
    "goals.md",
    "relationships.md",
    "recent-commits.md",
]


def iso_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_message():
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        line = line.strip()
        if line:
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue


def send_response(resp):
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()


def send_error(req_id, code, message):
    send_response(
        {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
    )


def run_git(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1


def get_git_history(path, limit=10):
    output, code = run_git(["git", "log", f"--oneline", f"-{limit}"], cwd=path)
    if code != 0:
        return []
    return [l.strip() for l in output.splitlines() if l.strip()]


def get_git_last_commit(path, rel_path):
    output, code = run_git(
        ["git", "log", "-1", "--format=%h %s %an", "--", rel_path], cwd=path
    )
    if code == 0 and output:
        return output.strip()
    return "unknown"


def get_file_modified(path, rel_path):
    full = os.path.join(path, rel_path)
    if not os.path.exists(full):
        return None
    mtime = os.path.getmtime(full)
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def freshness_score(path, rel_path):
    modified = get_file_modified(path, rel_path)
    if not modified:
        return "UNKNOWN"
    try:
        mtime = datetime.strptime(modified, "%Y-%m-%d %H:%M")
        age = (datetime.now(timezone.utc) - mtime.replace(tzinfo=timezone.utc)).days
        if age <= 1:
            return "HIGH"
        elif age <= 7:
            return "MEDIUM"
        else:
            return "LOW"
    except Exception:
        return "UNKNOWN"


def scan_repo(path):
    """Scan a repository and generate initial context files."""
    path = str(Path(path).expanduser().resolve())
    ctx_dir = os.path.join(path, CONTEXT_DIR)

    all_files = []
    code_files = []
    md_files = []

    for root, dirs, files in os.walk(path):
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".")
            and d
            not in (
                "node_modules",
                "__pycache__",
                "venv",
                ".venv",
                "build",
                "dist",
                "target",
            )
        ]
        for f in files:
            if f.startswith("."):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, path)
            all_files.append(rel)
            if f.endswith(
                (
                    ".py",
                    ".c",
                    ".cpp",
                    ".h",
                    ".hpp",
                    ".js",
                    ".ts",
                    ".jsx",
                    ".tsx",
                    ".go",
                    ".rs",
                    ".java",
                )
            ):
                code_files.append(rel)
            elif f.endswith(".md"):
                md_files.append(rel)

    os.makedirs(ctx_dir, exist_ok=True)

    recent_commits = get_git_history(path, limit=10)
    recent_commits_md = (
        "\n".join(f"- {c}" for c in recent_commits)
        if recent_commits
        else "- No commits found"
    )

    project_md = f"""# Project Overview

Generated: {iso_now()}

## Project Root
`{path}`

## Key Files
{len(all_files)} total files tracked.

## Code Files ({len(code_files)})
{chr(10).join(f"- {f}" for f in code_files[:30])}
{"... and more" if len(code_files) > 30 else ""}

## Markdown Docs
{chr(10).join(f"- {f}" for f in md_files)}
"""

    architecture_md = """# Architecture

## System Design
<!-- Fill in: describe the overall architecture, main components, data flow -->

## Directory Structure
<!-- Fill in: describe the key directories and their purposes -->

## Entry Points
<!-- Fill in: how to run, build, test the project -->
"""

    decisions_md = """# Decisions Log

## Why This File?
This file records significant technical decisions made during the project — the options considered, the choice made, and the reasoning behind it.

<!-- Add entries as decisions are made:

## [YYYY-MM-DD] Decision Title
**Status:** Accepted | Rejected | Deprecated

**Context:** What problem or question prompted this decision?

**Options Considered:**
- Option A: description
- Option B: description

**Decision:** Chosen approach

**Consequences:** What changed as a result?
-->
"""

    goals_md = f"""---
last_updated: {iso_now()}
---

# Long-term Goals
<!-- What is the overall vision for this project? What are you building toward? -->

# Short-term Goals
<!-- What is the current focus? What needs to be done next? -->

# Session History
- [{datetime.now().strftime("%Y-%m-%d")}] Project context initialized by context-maintainer
"""

    relationships_md = """# File Relationships

## Key Dependencies
<!-- Describe which files/modules depend on which. What affects what? -->

## Entry Point
<!-- Which file is the main entry point? -->
"""

    stale_files_md = f"""# Stale Files

## What is Stale?
Files or approaches marked here are deprecated or outdated. They are kept for reference but should not be used as examples of current practice.

## Deprecated Approaches
<!-- Add entries:

### filename or pattern
**Reason:** Why it is stale
**Date flagged:** YYYY-MM-DD
**Replaced by:** what replaced it
-->
"""

    active_files_md = f"""# Active Files

## What is Active?
Files being currently worked on or frequently modified. These are the primary targets for the agent's attention.

## Freshness Scores
- HIGH: modified < 24h
- MEDIUM: modified < 7 days
- LOW: modified > 7 days

## Active Files
<!-- Populated by update_context tool calls -->

## Recently Modified
"""

    files_written = {}
    contents = {
        "project.md": project_md,
        "architecture.md": architecture_md,
        "decisions.md": decisions_md,
        "goals.md": goals_md,
        "relationships.md": relationships_md,
        "stale-files.md": stale_files_md,
        "active-files.md": active_files_md,
        "recent-commits.md": f"# Recent Commits\n\nGenerated: {iso_now()}\n\n{recent_commits_md}",
    }

    for fname, content in contents.items():
        fpath = os.path.join(ctx_dir, fname)
        with open(fpath, "w") as fh:
            fh.write(content)
        files_written[fname] = len(content.splitlines())

    gitignore_path = os.path.join(path, ".gitignore")
    gitignore_content = ""
    if os.path.exists(gitignore_path):
        with open(gitignore_path) as f:
            gitignore_content = f.read()

    already_ignored = (
        ".context/" in gitignore_content or f"{CONTEXT_DIR}/" in gitignore_content
    )

    return {
        "success": True,
        "context_dir": ctx_dir,
        "files_created": list(contents.keys()),
        "gitignore_note": "already in .gitignore"
        if already_ignored
        else ".context/ NOT in .gitignore — run gitignore_add to exclude from commits",
    }


def update_context(path, file, summary, last_commit=None):
    """Update or add an entry in active-files.md."""
    path = str(Path(path).expanduser().resolve())
    ctx_file = os.path.join(path, CONTEXT_DIR, "active-files.md")
    if not os.path.exists(ctx_file):
        return {
            "success": False,
            "error": f"Context not initialized. Run init_context first.",
        }

    modified = get_file_modified(path, file)
    freshness = freshness_score(path, file)
    commit = last_commit or get_git_last_commit(path, file)

    marker = f"## {file}"
    new_entry = f"""{marker}
- **modified:** {modified or "unknown"}
- **last_commit:** {commit}
- **freshness:** {freshness}
- **summary:** {summary}
"""

    with open(ctx_file) as f:
        content = f.read()

    if marker in content:
        existing_pattern = re.compile(
            r"(## " + re.escape(file) + r".*?)(?=\n## |\n#|\Z)", re.DOTALL
        )
        content = existing_pattern.sub(new_entry.strip(), content, count=1)
    else:
        content = content.rstrip() + "\n\n" + new_entry

    with open(ctx_file, "w") as f:
        f.write(content)

    return {
        "success": True,
        "file": file,
        "freshness": freshness,
        "last_commit": commit,
    }


def checkpoint_goals(path, short_term, long_term):
    """Update goals.md with current goals."""
    path = str(Path(path).expanduser().resolve())
    goals_file = os.path.join(path, CONTEXT_DIR, "goals.md")
    if not os.path.exists(goals_file):
        return {
            "success": False,
            "error": "Context not initialized. Run init_context first.",
        }

    with open(goals_file) as f:
        content = f.read()

    lt_lines = (
        "\n".join(f"- {s}" for s in long_term)
        if isinstance(long_term, list)
        else str(long_term)
    )
    st_lines = (
        "\n".join(f"- {s}" for s in short_term)
        if isinstance(short_term, list)
        else str(short_term)
    )

    content = re.sub(
        r"(?<=^# Long-term Goals\n).*?(?=\n#)",
        f"\n{lt_lines}\n",
        content,
        flags=re.DOTALL | re.MULTILINE,
    )
    content = re.sub(
        r"(?<=^# Short-term Goals\n).*?(?=\n#|\Z)",
        f"\n{st_lines}\n",
        content,
        flags=re.DOTALL | re.MULTILINE,
    )
    content = re.sub(r"last_updated:.*", f"last_updated: {iso_now()}", content)

    session_entry = f"- [{datetime.now().strftime('%Y-%m-%d')}] Goals checkpointed"
    if "## Session History" not in content:
        content += f"\n\n## Session History\n{session_entry}\n"
    else:
        content = re.sub(
            r"(?<=## Session History\n).*?(?=\n#|\Z)",
            lambda m: (m.group() or "").rstrip() + f"\n{session_entry}\n",
            content,
            flags=re.DOTALL,
        )

    with open(goals_file, "w") as f:
        f.write(content)

    return {"success": True, "last_updated": iso_now()}


def flag_stale(path, pattern, reason):
    """Flag a file/pattern as stale in stale-files.md."""
    path = str(Path(path).expanduser().resolve())
    stale_file = os.path.join(path, CONTEXT_DIR, "stale-files.md")
    active_file = os.path.join(path, CONTEXT_DIR, "active-files.md")
    if not os.path.exists(stale_file):
        return {"success": False, "error": "Context not initialized."}

    entry = f"""
### {pattern}
**Reason:** {reason}
**Date flagged:** {datetime.now().strftime("%Y-%m-%d")}
"""
    with open(stale_file) as f:
        content = f.read()
    content = content.rstrip() + "\n" + entry
    with open(stale_file, "w") as f:
        f.write(content)

    if os.path.exists(active_file):
        with open(active_file) as f:
            active = f.read()
        marker = f"## {pattern}"
        if marker in active:
            active = re.sub(
                r"(## " + re.escape(pattern) + r".*?)(?=\n## |\n#|\Z)",
                f"## {pattern} # STALE",
                active,
                count=1,
                flags=re.DOTALL,
            )
            with open(active_file, "w") as f:
                f.write(active)

    return {"success": True, "pattern": pattern, "reason": reason}


def promote_stale(path, pattern):
    """Remove stale flag from a pattern."""
    path = str(Path(path).expanduser().resolve())
    stale_file = os.path.join(path, CONTEXT_DIR, "stale-files.md")
    active_file = os.path.join(path, CONTEXT_DIR, "active-files.md")
    if not os.path.exists(stale_file):
        return {"success": False, "error": "Context not initialized."}

    with open(stale_file) as f:
        content = f.read()
    entry_pattern = re.compile(
        r"\n+### " + re.escape(pattern) + r".*?(?=\n### |\n#|\Z)", re.DOTALL
    )
    removed = bool(entry_pattern.search(content))
    if removed:
        content = entry_pattern.sub("", content)
        with open(stale_file, "w") as f:
            f.write(content)

    if os.path.exists(active_file):
        with open(active_file) as f:
            active = f.read()
        active = active.replace(f"## {pattern} # STALE", f"## {pattern}")
        freshness = freshness_score(path, pattern)
        with open(active_file, "w") as f:
            f.write(active)

    return {"success": True, "pattern": pattern, "removed_stale": removed}


def gitignore_add(path):
    """Add .context/ to .gitignore."""
    path = str(Path(path).expanduser().resolve())
    gi_path = os.path.join(path, ".gitignore")
    if os.path.exists(gi_path):
        with open(gi_path) as f:
            content = f.read()
    else:
        content = ""
    if ".context/" not in content:
        content += "\n.context/\n"
        with open(gi_path, "w") as f:
            f.write(content)
    return {"success": True, "path": gi_path, "added": ".context/"}


def gitignore_remove(path):
    """Remove .context/ from .gitignore (opt-in to track)."""
    path = str(Path(path).expanduser().resolve())
    gi_path = os.path.join(path, ".gitignore")
    if not os.path.exists(gi_path):
        return {"success": False, "error": ".gitignore not found"}
    with open(gi_path) as f:
        lines = f.readlines()
    new_lines = [l for l in lines if ".context/" not in l.rstrip("\n")]
    with open(gi_path, "w") as f:
        f.writelines(new_lines)
    return {"success": True, "path": gi_path, "removed": ".context/"}


def gitignore_status(path):
    """Check if .context/ is in .gitignore."""
    path = str(Path(path).expanduser().resolve())
    gi_path = os.path.join(path, ".gitignore")
    if not os.path.exists(gi_path):
        return {
            "tracked": True,
            "path": gi_path,
            "note": ".gitignore doesn't exist — context would be tracked by default",
        }
    with open(gi_path) as f:
        content = f.read()
    ignored = ".context/" in content or f"{CONTEXT_DIR}/" in content
    return {"tracked": not ignored, "path": gi_path}


TOOLS = [
    {
        "name": "init_context",
        "description": "Initialize .context/ directory in a project. Scans the repo, generates all context files, and optionally adds .context/ to .gitignore.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the project root"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "update_context",
        "description": "Update or add an entry in active-files.md with file summary and git history.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "file": {
                    "type": "string",
                    "description": "File path relative to project root",
                },
                "summary": {
                    "type": "string",
                    "description": "Brief description of the file's purpose or recent changes",
                },
                "last_commit": {
                    "type": "string",
                    "description": "Optional: last git commit for this file",
                },
            },
            "required": ["path", "file", "summary"],
        },
    },
    {
        "name": "checkpoint_goals",
        "description": "Update goals.md with current short-term and long-term goals.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "short_term": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Current short-term goals",
                },
                "long_term": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Long-term goals",
                },
            },
            "required": ["path", "short_term", "long_term"],
        },
    },
    {
        "name": "flag_stale",
        "description": "Mark a file or pattern as deprecated/stale.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "pattern": {
                    "type": "string",
                    "description": "File name or glob pattern",
                },
                "reason": {"type": "string", "description": "Why it is stale"},
            },
            "required": ["path", "pattern", "reason"],
        },
    },
    {
        "name": "promote_stale",
        "description": "Remove stale flag from a pattern, restoring it to active.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "pattern": {"type": "string"}},
            "required": ["path", "pattern"],
        },
    },
    {
        "name": "gitignore_add",
        "description": "Add .context/ to .gitignore to prevent committing context files.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "gitignore_remove",
        "description": "Remove .context/ from .gitignore to opt-in to committing context.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "gitignore_status",
        "description": "Check whether .context/ is currently in .gitignore.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
]


def handle_request(req):
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params", {})
    args = params.get("arguments", {})

    if method == "initialize":
        send_response(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "context-maintainer-mcp",
                        "version": "1.0.0",
                    },
                },
            }
        )
        return

    if method == "tools/list":
        send_response({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})
        return

    if method == "tools/call":
        tool_name = args.get("name")
        tool_args = {k: v for k, v in args.items() if k not in ("name",)}

        if tool_name == "init_context":
            result = scan_repo(**tool_args)
        elif tool_name == "update_context":
            result = update_context(**tool_args)
        elif tool_name == "checkpoint_goals":
            result = checkpoint_goals(**tool_args)
        elif tool_name == "flag_stale":
            result = flag_stale(**tool_args)
        elif tool_name == "promote_stale":
            result = promote_stale(**tool_args)
        elif tool_name == "gitignore_add":
            result = gitignore_add(**tool_args)
        elif tool_name == "gitignore_remove":
            result = gitignore_remove(**tool_args)
        elif tool_name == "gitignore_status":
            result = gitignore_status(**tool_args)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        send_response(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
            }
        )
        return

    send_error(req_id, -32601, f"Method not found: {method}")


def main():
    while True:
        msg = read_message()
        if msg is None:
            break
        handle_request(msg)


if __name__ == "__main__":
    main()
