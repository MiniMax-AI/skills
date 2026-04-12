#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
context-search MCP server — search .context/ files for AI coding agents.

Usage:
    uvx context-search-mcp

Provides tools for searching and retrieving context from .context/ directories.
Includes optional QMD integration for hybrid semantic search.

Environment:
    No external dependencies — Python stdlib only.
    QMD integration requires qmd to be installed separately.
"""

import os
import sys
import json
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

CONTEXT_DIR = ".context"

QMD_CHECKED = False
QMD_AVAILABLE = False


def check_qmd():
    global QMD_CHECKED, QMD_AVAILABLE
    if QMD_CHECKED:
        return QMD_AVAILABLE
    QMD_CHECKED = True
    result = subprocess.run(["which", "qmd"], capture_output=True, text=True)
    if result.returncode == 0:
        QMD_AVAILABLE = True
    return QMD_AVAILABLE


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


def get_context_files(path):
    ctx_dir = os.path.join(path, CONTEXT_DIR)
    if not os.path.isdir(ctx_dir):
        return None, f"Context directory not found: {ctx_dir}"
    files = {}
    for f in os.listdir(ctx_dir):
        if f.endswith(".md"):
            fpath = os.path.join(ctx_dir, f)
            with open(fpath) as fh:
                files[f] = fh.read()
    return files, None


def grep_in_context(path, pattern, max_results=10):
    """Simple grep-based search across all .context/ files."""
    files, err = get_context_files(path)
    if err:
        return {"results": [], "error": err}

    results = []
    pattern_lower = pattern.lower()
    for fname, content in files.items():
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if pattern_lower in line.lower():
                snippet = line.strip()[:120]
                context_before = []
                context_after = []
                for j in range(max(0, i - 3), i):
                    context_before.append((j + 1, lines[j].strip()[:120]))
                for j in range(i, min(len(lines), i + 2)):
                    if j != i - 1:
                        context_after.append((j + 1, lines[j].strip()[:120]))
                score = 1.0 if pattern_lower in snippet.lower() else 0.5
                results.append(
                    {
                        "file": fname,
                        "line": i,
                        "text": snippet,
                        "context_before": context_before,
                        "context_after": context_after,
                        "score": score,
                    }
                )
                if len(results) >= max_results:
                    break
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": results, "count": len(results)}


def search_context(query, path=None):
    """Search .context/ files. If QMD is available, delegate to qmd query."""
    if not path:
        return {"results": [], "error": "path is required"}

    ctx_dir = os.path.join(path, CONTEXT_DIR)
    if not os.path.isdir(ctx_dir):
        return {"results": [], "error": f"Context not initialized at {ctx_dir}"}

    if check_qmd():
        try:
            result = subprocess.run(
                ["qmd", "query", query, "--json", "-n", "10"],
                cwd=ctx_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                parsed = json.loads(result.stdout)
                return {
                    "results": parsed.get("results", []),
                    "engine": "qmd",
                    "note": "QMD hybrid search (BM25 + vector + reranking)",
                }
        except Exception:
            pass

    results = grep_in_context(path, query)
    results["engine"] = "grep"
    results["note"] = "Simple grep search. Install qmd for hybrid semantic search."
    return results


def get_active_context(path):
    """Return all non-stale context entries."""
    files, err = get_context_files(path)
    if err:
        return {"active": {}, "error": err}

    active = {}
    for fname, content in files.items():
        stale_marker = "# STALE" in content or "# stale" in content.lower()
        if not stale_marker:
            preview = content[:300].strip()
            active[fname] = {"preview": preview, "lines": len(content.splitlines())}
        else:
            active[fname] = {
                "preview": "[STALE — see stale-files.md]",
                "lines": len(content.splitlines()),
                "stale": True,
            }

    return {"active": active, "count": len(active)}


def get_file_context(path, filename):
    """Get context entry for a specific file from active-files.md."""
    active_file = os.path.join(path, CONTEXT_DIR, "active-files.md")
    if not os.path.exists(active_file):
        return {"entry": None, "error": f"active-files.md not found at {active_file}"}

    with open(active_file) as f:
        content = f.read()

    marker = f"## {filename}"
    if marker not in content:
        return {"entry": None, "found": False, "note": f"No entry found for {filename}"}

    entry = re.search(
        r"## " + re.escape(filename) + r".*?(?=\n## |\n#|\Z)", content, re.DOTALL
    )
    if entry:
        return {"entry": entry.group().strip(), "found": True, "file": filename}
    return {"entry": None, "found": False}


def export_to_vault(context_path, vault_path):
    """Copy .context/ files to an Obsidian vault directory."""
    ctx_dir = os.path.join(context_path, CONTEXT_DIR)
    if not os.path.isdir(ctx_dir):
        return {"success": False, "error": f"No .context/ directory at {ctx_dir}"}

    vault = Path(vault_path).expanduser().resolve()
    os.makedirs(vault, exist_ok=True)

    exported = []
    for f in os.listdir(ctx_dir):
        if f.endswith(".md"):
            src = os.path.join(ctx_dir, f)
            dst = vault / f
            shutil.copy2(src, dst)
            exported.append(f)

    return {
        "success": True,
        "vault_path": str(vault),
        "exported": exported,
        "count": len(exported),
        "note": "Context exported to Obsidian vault. You can now use Obsidian's graph view to explore relationships.",
    }


def prune_context(path, older_than_days=30):
    """Remove stale entries older than N days from stale-files.md."""
    stale_file = os.path.join(path, CONTEXT_DIR, "stale-files.md")
    if not os.path.exists(stale_file):
        return {"pruned": 0, "error": "stale-files.md not found"}

    cutoff = datetime.now(timezone.utc).timestamp() - (older_than_days * 86400)
    with open(stale_file) as f:
        content = f.read()

    lines = content.splitlines()
    new_lines = []
    removed = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if "**Date flagged:**" in line:
            date_str = line.split("**Date flagged:**")[1].strip()
            try:
                flagged_date = (
                    datetime.strptime(date_str, "%Y-%m-%d")
                    .replace(tzinfo=timezone.utc)
                    .timestamp()
                )
                if flagged_date < cutoff:
                    while i < len(lines) and not (
                        lines[i].startswith("### ") and i > 0
                    ):
                        i += 1
                    removed += 1
                    continue
            except ValueError:
                pass
        new_lines.append(line)
        i += 1

    with open(stale_file, "w") as f:
        f.write("\n".join(new_lines))

    return {"success": True, "pruned": removed, "older_than_days": older_than_days}


def check_qmd_status():
    """Check if QMD is available and what version."""
    if not check_qmd():
        return {
            "available": False,
            "note": "QMD not found. Install with: npm install -g @tobilu/qmd",
        }
    try:
        result = subprocess.run(["qmd", "--version"], capture_output=True, text=True)
        version = result.stdout.strip() if result.returncode == 0 else "unknown"
        return {"available": True, "version": version}
    except Exception:
        return {"available": True, "note": "QMD found but version check failed"}


TOOLS = [
    {
        "name": "search_context",
        "description": "Search .context/ files for a query. Uses grep by default; if QMD is available, delegates to QMD for hybrid semantic search.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "path": {"type": "string", "description": "Path to project root"},
            },
            "required": ["query", "path"],
        },
    },
    {
        "name": "get_active_context",
        "description": "Return all non-stale context entries as a readable summary.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to project root"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "get_file_context",
        "description": "Get context entry for a specific file from active-files.md.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "filename": {
                    "type": "string",
                    "description": "File name (not full path)",
                },
            },
            "required": ["path", "filename"],
        },
    },
    {
        "name": "export_to_vault",
        "description": "Copy .context/ files to an Obsidian vault directory for graph exploration.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "context_path": {
                    "type": "string",
                    "description": "Path to project root containing .context/",
                },
                "vault_path": {
                    "type": "string",
                    "description": "Path to Obsidian vault directory",
                },
            },
            "required": ["context_path", "vault_path"],
        },
    },
    {
        "name": "prune_context",
        "description": "Remove stale entries older than N days from stale-files.md.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "older_than_days": {"type": "integer", "default": 30},
            },
            "required": ["path"],
        },
    },
    {
        "name": "check_qmd",
        "description": "Check if QMD is available on the system for optional semantic search.",
        "inputSchema": {"type": "object", "properties": {}},
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
                    "serverInfo": {"name": "context-search-mcp", "version": "1.0.0"},
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

        if tool_name == "search_context":
            result = search_context(**tool_args)
        elif tool_name == "get_active_context":
            result = get_active_context(**tool_args)
        elif tool_name == "get_file_context":
            result = get_file_context(**tool_args)
        elif tool_name == "export_to_vault":
            result = export_to_vault(**tool_args)
        elif tool_name == "prune_context":
            result = prune_context(**tool_args)
        elif tool_name == "check_qmd":
            result = check_qmd_status()
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
