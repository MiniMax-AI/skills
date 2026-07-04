#!/usr/bin/env python3
"""Validate skill directory structure and SKILL.md frontmatter.

Zero external dependencies — uses only Python standard library.
Exit code 0: all checks passed (warnings are OK).
Exit code 1: at least one ERROR found.

Usage:
    python validate_skills.py                    # scan default path (skills/)
    python validate_skills.py --path some/dir    # scan specific directory
"""

import argparse
import os
import re
import sys


# ---------------------------------------------------------------------------
# Minimal frontmatter parser
# ---------------------------------------------------------------------------
def extract_frontmatter(text):
    """Extract YAML frontmatter string between --- markers. Returns None if not found."""
    stripped = text.lstrip("\ufeff")
    lines = stripped.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for idx, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return "\n".join(lines[1:idx])
    return None


def has_legacy_metadata_outside_frontmatter(text):
    """Detect common legacy files with name/description lines outside YAML frontmatter."""
    stripped = text.lstrip("\ufeff")
    if stripped.startswith("---"):
        return False
    header = "\n".join(stripped.splitlines()[:12])
    has_name = re.search(r"(?m)^name\s*:\s*\S+", header) is not None
    has_description = re.search(r"(?m)^description\s*:\s*\S+", header) is not None
    return has_name and has_description


def parse_frontmatter_fields(fm_text):
    """Parse top-level scalar fields from frontmatter text.

    Returns dict of {field_name: value_string}. Nested keys under a mapping
    are ignored — we only need top-level presence checks.
    """
    fields = {}
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)", line)
        if m:
            key = m.group(1)
            rest = m.group(2).strip()
            if rest in ("|", ">", "|+", "|-", ">+", ">-"):
                block_lines = []
                i += 1
                while i < len(lines) and (lines[i].startswith("  ") or lines[i].startswith("\t") or lines[i].strip() == ""):
                    block_lines.append(lines[i])
                    i += 1
                fields[key] = "\n".join(block_lines).strip()
                continue
            elif rest == "":
                block_lines = []
                i += 1
                while i < len(lines) and (lines[i].startswith("  ") or lines[i].startswith("\t")):
                    block_lines.append(lines[i])
                    i += 1
                fields[key] = "\n".join(block_lines).strip() if block_lines else ""
                continue
            else:
                fields[key] = rest.strip("\"'")
        i += 1
    return fields


# ---------------------------------------------------------------------------
# Secret scanning
# ---------------------------------------------------------------------------
SECRET_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI-style API key"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"Bearer\s+[a-zA-Z0-9_\-\.]{50,}", "Hardcoded bearer token"),
]

SCAN_EXTENSIONS = {".md", ".py", ".sh", ".js", ".ts", ".json", ".yaml", ".yml", ".txt", ".toml", ".cfg", ".ini"}

def scan_secrets(filepath):
    """Scan a file for hardcoded secrets. Returns list of (line_no, pattern_desc, matched_text)."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return []

    findings = []
    for line_no, line in enumerate(content.splitlines(), 1):
        for pattern, desc in SECRET_PATTERNS:
            for match in re.finditer(pattern, line):
                findings.append((line_no, desc, match.group(0)[:60]))
    return findings


# ---------------------------------------------------------------------------
# Skill discovery and validation
# ---------------------------------------------------------------------------
def find_skill_dirs(base_path):
    """Find directories that contain a SKILL.md."""
    skill_dirs = []
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        if "SKILL.md" in files:
            skill_dirs.append(root)
    return sorted(skill_dirs)


def validate_skill(skill_dir):
    """Validate a single skill directory. Returns (errors, warnings) lists."""
    errors = []
    warnings = []
    dir_name = os.path.basename(skill_dir)
    skill_md = os.path.join(skill_dir, "SKILL.md")

    if not os.path.isfile(skill_md):
        errors.append("SKILL.md not found")
        return errors, warnings

    with open(skill_md, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    fm_text = extract_frontmatter(content)
    if fm_text is None:
        if has_legacy_metadata_outside_frontmatter(content):
            errors.append(
                "SKILL.md has name/description outside YAML frontmatter; "
                "wrap required metadata between opening and closing --- markers"
            )
        else:
            errors.append("SKILL.md has no valid YAML frontmatter (missing --- markers)")
        return errors, warnings

    fields = parse_frontmatter_fields(fm_text)

    name = fields.get("name", "").strip()
    if not name:
        errors.append("Missing required field: name")
    elif name != dir_name:
        errors.append(f"name '{name}' does not match directory name '{dir_name}'")

    desc = fields.get("description", "").strip()
    if not desc:
        errors.append("Missing required field: description")

    if "license" not in fields or not fields["license"].strip():
        warnings.append("Missing recommended field: license")

    if "metadata" not in fields or not fields["metadata"].strip():
        warnings.append("Missing recommended field: metadata")

    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            _, ext = os.path.splitext(fname)
            if ext not in SCAN_EXTENSIONS:
                continue
            fpath = os.path.join(root, fname)
            for line_no, sdesc, matched in scan_secrets(fpath):
                rel = os.path.relpath(fpath, skill_dir)
                errors.append(f"Potential secret in {rel}:{line_no} ({sdesc}): {matched}...")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate MiniMax Skills structure")
    parser.add_argument("--path", default="skills", help="Directory to scan (default: skills/)")
    args = parser.parse_args()

    scan_path = os.path.abspath(args.path)

    skill_dirs = find_skill_dirs(scan_path)
    if not skill_dirs:
        print("No skill directories found.")
        sys.exit(0)

    print(f"\nValidating {len(skill_dirs)} skill(s)...\n")

    total_errors = 0
    total_warnings = 0

    for sd in skill_dirs:
        rel = os.path.relpath(sd)
        errors, warnings = validate_skill(sd)

        if errors:
            status = "FAIL"
        elif warnings:
            status = "WARN"
        else:
            status = "PASS"

        print(f"  [{status}]  {rel}")
        for msg in errors:
            print(f"           ERROR  {msg}")
        for msg in warnings:
            print(f"           WARN   {msg}")

        total_errors += len(errors)
        total_warnings += len(warnings)

    print()
    if total_errors:
        print(f"  {total_errors} error(s), {total_warnings} warning(s)")
        print("  Validation FAILED.\n")
        sys.exit(1)
    elif total_warnings:
        print(f"  0 errors, {total_warnings} warning(s)")
        print("  Validation PASSED.\n")
    else:
        print("  All checks passed.\n")


if __name__ == "__main__":
    main()
