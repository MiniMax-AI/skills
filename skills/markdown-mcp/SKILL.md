---
name: markdown-mcp
description: >
  Use the markdown-mcp tool for all markdown file operations. Load this skill when you need to
  read, edit, search, or modify any markdown (.md) file. Replaces the pattern of writing Python
  scripts to manipulate files — use the MCP tools directly instead.
  Triggers: any time you need to edit a markdown file, read a markdown file, search within a
  markdown file, add content to a markdown file, update a table in markdown, insert text into
  a markdown file, or replace text in a markdown file.
license: MIT
metadata:
  version: "1.0"
  category: productivity
  tools: markdown-mcp
---

# Markdown MCP Tools

Use these tools for all markdown file operations. **Never write Python scripts to edit files.**

## Prerequisites

The `minimax-markdown-mcp` MCP server must be installed and configured.

**OpenCode** — add to `~/.config/opencode/opencode.json` or `package.json`:
```json
{
  "mcp": {
    "markdown-mcp": {
      "type": "local",
      "command": ["uvx", "minimax-markdown-mcp"],
      "enabled": true
    }
  }
}
```

**Cursor** — add to MCP settings:
```json
{
  "mcpServers": {
    "markdown-mcp": {
      "command": "uvx",
      "args": ["minimax-markdown-mcp"]
    }
  }
}
```

Restart the app after configuring. Verify with `/mcp` — `markdown-mcp` should appear.

## Available Tools

| Tool | When to use |
|---|---|
| `get_file_info` | Check line count, headers, tables — instant, no content read |
| `grep_lines` | Find a pattern in a file — returns line numbers + snippets |
| `read_section` | Read a specific section by pattern or line offsets |
| `replace_text` | Replace exact text — for small targeted changes |
| `insert_after_line` | Insert text after a specific line number |
| `append_line` | Append text to end of file |

---

## Core Workflow

**Never do this:** write a Python script → run it → debug → repeat.

**Always do this:**

### To understand a file before editing:

```
1. get_file_info(path="/path/to/file.md")
   → tells you line count, section headers, table presence
2. grep_lines(path="/path/to/file.md", pattern="search term", context=2)
   → shows line numbers + snippets around matches
3. read_section(path="/path/to/file.md", start_pat="## Section", end_pat="## Next Section")
   → reads only that section
```

### To make a targeted change:

```
replace_text(path="/path/to/file.md", old_text="exact text to replace", new_text="new text", max_count=1)
```

### To insert content (e.g., new section after an existing one):

```
1. grep_lines(path="/path/to/file.md", pattern="## Previous Section")
   → get the line number
2. insert_after_line(path="/path/to/file.md", after_line=N, text="## New Section\n\nContent.")
```

### To add to the end of a file:

```
append_line(path="/path/to/file.md", text="## New Section\n\nContent.")
```

---

## When to Use Each Tool

### get_file_info — always start here
- No content read, just structure
- Tells you line count, headers, whether there are tables
- Use before grepping if you don't know the file structure

### grep_lines — find content fast
- No full file read
- Returns line numbers + snippets with context lines
- Use to locate sections before editing

### read_section — targeted reading
- Read only between two patterns, or between line offsets
- Never read an entire large file
- max 100 lines per call for large sections

### replace_text — exact replacement
- For small text changes (a phrase, a table row, a code snippet)
- old_text must match EXACTLY including whitespace
- max_count=1 by default (change one occurrence at a time)

### insert_after_line — precise insertion
- Insert new content after a specific line number
- Use grep_lines to find the right line first
- text can be multi-line (separate lines with \n)

### append_line — end of file
- For adding new sections at the end
- Simpler than insert_after_line when you don't need precise placement

---

## Common Tasks

### Add a new change entry to an existing table

```
1. grep_lines(path="opt_log.md", pattern="Change\t", context=1)
   → find where the table is
2. read_section(path="opt_log.md", start_pat="Change\t", end_pat="\n##")
   → read the table
3. replace_text(path="opt_log.md", old_text="5c\t...", new_text="5c\t...\n5d\t...")
```

### Insert a new section between existing sections

```
1. grep_lines(path="file.md", pattern="## Existing Section")
   → get line number
2. insert_after_line(path="file.md", after_line=N, text="## New Section\n\n...")
```

### Replace a specific code block

```
1. grep_lines(path="file.md", pattern="```c", context=3)
   → find the code block
2. replace_text(path="file.md", old_text="```c\nOLD CODE\n```", new_text="```c\nNEW CODE\n```")
```

---

## File Size Rules

| Size | Rule |
|---|---|
| Any size | Always `get_file_info` first |
| < 100 lines | Can `read_section` with wide offset |
| > 100 lines | Always `grep_lines` first, then targeted `read_section` |
| > 500 lines | Never read fully. Break into sections via grep |

---

## Anti-Patterns

- ❌ Writing and running a Python script to edit a file
- ❌ Reading the entire file with `read_section` using large offsets
- ❌ Using `replace_text` with old_text that doesn't exactly match
- ❌ Running `grep` via bash instead of using `grep_lines`
- ❌ Making multiple edits without checking each one's result

## Output Rules

After each tool call:
- If success: brief confirmation only ("Done.", "Replaced 1 occurrence.")
- If failure: state the error and what you tried ("replace_text failed: 'pattern' not found. Did you mean...?")
- Never output the full file content after editing
