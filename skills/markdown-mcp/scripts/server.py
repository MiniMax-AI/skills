#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
minimax-markdown-mcp — MCP server for efficient markdown file reading and editing.

Usage:
    uvx minimax-markdown-mcp

Environment:
    MINIMAX_API_KEY (optional, not required for local file operations)
    MINIMAX_API_HOST (optional, defaults to https://api.minimaxi.com)

No external file operation dependencies — uses only stdlib.
"""

import os
import sys
import json
import re
from pathlib import Path

STDIO_HEADER = "application/json"


def read_message():
    """Read a JSON-RPC message from stdin."""
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
    return None


def send_response(resp):
    """Send a JSON-RPC response to stdout."""
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()


def send_error(req_id, code, message):
    """Send a JSON-RPC error."""
    send_response(
        {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
    )


def read_section(
    path: str,
    start_pat: str = None,
    end_pat: str = None,
    start_offset: int = 0,
    end_offset: int = None,
):
    """
    Read a section of a file.

    Either by pattern (start_pat/end_pat) or by line offsets.
    Returns {"content": "...", "start_line": N, "end_line": N, "total_lines": N}
    """
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return {
                "content": "",
                "start_line": 0,
                "end_line": 0,
                "total_lines": 0,
                "error": f"File not found: {path}",
            }

        lines = p.read_text().splitlines()
        total = len(lines)

        if start_pat is not None:
            start_idx = next((i for i, l in enumerate(lines) if start_pat in l), None)
            if start_idx is None:
                return {
                    "content": "",
                    "start_line": 0,
                    "end_line": total,
                    "total_lines": total,
                    "error": f"Pattern not found: {start_pat}",
                }
            if end_pat is not None:
                end_idx = next(
                    (
                        i
                        for i, l in enumerate(
                            lines[start_idx + 1 :], start=start_idx + 1
                        )
                        if end_pat in l
                    ),
                    None,
                )
                if end_idx is None:
                    end_idx = total - 1
            else:
                end_idx = min(start_idx + 100, total - 1)
        else:
            start_idx = start_offset
            end_idx = (
                end_offset
                if end_offset is not None
                else min(start_idx + 100, total - 1)
            )

        end_idx = min(end_idx, total - 1)
        content = "\n".join(lines[start_idx : end_idx + 1])
        return {
            "content": content,
            "start_line": start_idx + 1,
            "end_line": end_idx + 1,
            "total_lines": total,
        }

    except Exception as e:
        return {
            "content": "",
            "start_line": 0,
            "end_line": 0,
            "total_lines": 0,
            "error": str(e),
        }


def get_file_info(path: str):
    """Get file structure info without reading content."""
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return {
                "exists": False,
                "line_count": 0,
                "headers": [],
                "error": f"File not found: {path}",
            }

        lines = p.read_text().splitlines()
        headers = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (
                stripped.startswith("# ")
                or stripped.startswith("## ")
                or stripped.startswith("### ")
            ):
                headers.append(
                    {
                        "level": len(stripped) - len(stripped.lstrip("#")),
                        "line": i + 1,
                        "text": stripped.lstrip("# ").strip()[:80],
                    }
                )

        return {
            "exists": True,
            "line_count": len(lines),
            "size_bytes": p.stat().st_size,
            "headers": headers[:50],
            "has_tables": bool(re.search(r"\|.*\|.*\|", "\n".join(lines[:100]))),
        }
    except Exception as e:
        return {"exists": False, "line_count": 0, "headers": [], "error": str(e)}


def grep_lines(path: str, pattern: str, context: int = 0):
    """Find all lines matching a pattern. Returns line numbers + snippets."""
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return {"matches": [], "count": 0, "error": f"File not found: {path}"}

        lines = p.read_text().splitlines()
        matches = []
        for i, line in enumerate(lines):
            if pattern in line:
                snippet = line.strip()[:120]
                if context > 0:
                    before = [
                        (j + 1, lines[j].strip()[:120])
                        for j in range(max(0, i - context), i)
                    ]
                    after = [
                        (j + 1, lines[j].strip()[:120])
                        for j in range(i + 1, min(len(lines), i + context + 1))
                    ]
                else:
                    before, after = [], []
                matches.append(
                    {"line": i + 1, "text": snippet, "before": before, "after": after}
                )

        return {"matches": matches, "count": len(matches)}
    except Exception as e:
        return {"matches": [], "count": 0, "error": str(e)}


def insert_after_line(path: str, after_line: int, text: str):
    """Insert text after a specific line number. Lines are 1-indexed."""
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return {"success": False, "error": f"File not found: {path}"}

        lines = p.read_text().splitlines()
        total = len(lines)

        if after_line < 1 or after_line > total:
            return {
                "success": False,
                "error": f"Line {after_line} out of range (1-{total})",
            }

        new_lines = lines[:after_line]
        new_lines.extend(text.splitlines())
        new_lines.extend(lines[after_line:])

        p.write_text("\n".join(new_lines) + "\n")
        return {
            "success": True,
            "new_total_lines": len(new_lines),
            "inserted_after": after_line,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def replace_text(path: str, old_text: str, new_text: str, max_count: int = 1):
    """Replace exact old_text with new_text. max_count=0 means replace all."""
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return {"success": False, "replaced": 0, "error": f"File not found: {path}"}

        content = p.read_text()
        if old_text not in content:
            return {"success": False, "replaced": 0, "error": "Text not found in file"}

        if max_count > 0:
            new_content = content.replace(old_text, new_text, max_count)
        else:
            new_content = content.replace(old_text, new_text)

        replaced = (
            content.count(old_text)
            if max_count == 0
            else min(content.count(old_text), max_count)
        )
        p.write_text(new_content)
        return {"success": True, "replaced": replaced}
    except Exception as e:
        return {"success": False, "replaced": 0, "error": str(e)}


def append_line(path: str, text: str):
    """Append a line or block of text to the end of a file."""
    try:
        p = Path(path).expanduser()
        existing = p.read_text() if p.exists() else ""
        if existing and not existing.endswith("\n"):
            existing += "\n"
        p.write_text(existing + text + "\n")
        new_lines = (existing + text + "\n").splitlines()
        return {"success": True, "appended_after_line": len(existing.splitlines())}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_request(req):
    """Handle an MCP JSON-RPC request."""
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        send_response(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "minimax-markdown-mcp", "version": "1.0.0"},
                },
            }
        )
        return

    if method == "tools/list":
        send_response(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "get_file_info",
                            "description": "Get file structure (line count, headers, tables) without reading content.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"path": {"type": "string"}},
                                "required": ["path"],
                            },
                        },
                        {
                            "name": "grep_lines",
                            "description": "Find lines matching a pattern. Returns line numbers + snippets.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "pattern": {"type": "string"},
                                    "context": {"type": "integer", "default": 0},
                                },
                                "required": ["path", "pattern"],
                            },
                        },
                        {
                            "name": "read_section",
                            "description": "Read a section of a file by pattern or line offsets.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "start_pat": {"type": "string"},
                                    "end_pat": {"type": "string"},
                                    "start_offset": {"type": "integer", "default": 0},
                                    "end_offset": {"type": "integer"},
                                },
                                "required": ["path"],
                            },
                        },
                        {
                            "name": "insert_after_line",
                            "description": "Insert text after a specific line number.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "after_line": {"type": "integer"},
                                    "text": {"type": "string"},
                                },
                                "required": ["path", "after_line", "text"],
                            },
                        },
                        {
                            "name": "replace_text",
                            "description": "Replace exact old_text with new_text in a file.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "old_text": {"type": "string"},
                                    "new_text": {"type": "string"},
                                    "max_count": {"type": "integer", "default": 1},
                                },
                                "required": ["path", "old_text", "new_text"],
                            },
                        },
                        {
                            "name": "append_line",
                            "description": "Append text to end of file.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "text": {"type": "string"},
                                },
                                "required": ["path", "text"],
                            },
                        },
                    ]
                },
            }
        )
        return

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if tool_name == "get_file_info":
            result = get_file_info(**tool_args)
        elif tool_name == "grep_lines":
            result = grep_lines(**tool_args)
        elif tool_name == "read_section":
            result = read_section(**tool_args)
        elif tool_name == "insert_after_line":
            result = insert_after_line(**tool_args)
        elif tool_name == "replace_text":
            result = replace_text(**tool_args)
        elif tool_name == "append_line":
            result = append_line(**tool_args)
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
    """Main loop — read JSON-RPC messages from stdin."""
    while True:
        msg = read_message()
        if msg is None:
            break
        handle_request(msg)


if __name__ == "__main__":
    main()
