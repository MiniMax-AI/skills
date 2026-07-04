#!/usr/bin/env python3
"""
fix-skill-frontmatter.py — audit and repair SKILL.md files used by
MiniMax Code / OpenCode / Claude Code / Cursor / Codex skills.

Detects two frontmatter shapes:

  Shape A — correct YAML block at the top:
    ---
    name: foo
    description: One-line summary.
    ---

  Shape B — legacy human-readable header:
    # Skill: Foo
    name: foo
    description: One-line summary.
    ## Section
    ...

Repairs Shape B by extracting `name:` / `description:` and prepending
a fresh YAML block at the top, dropping the duplicate inline copy.

Usage:
    python3 fix-skill-frontmatter.py --dry [--skills-dir DIR]
    python3 fix-skill-frontmatter.py [--skills-dir DIR]

Defaults: SKILLS_DIR=$HOME/.minimax/skills (or pass --skills-dir).
Idempotent: leaves already-valid files untouched.
Atomic per-file: writes to a `.tmp` sibling, then `os.replace`.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple

DEFAULT_DIR = Path.home() / ".minimax" / "skills"

DEFAULT_TARGETS = (
    # Add more skills here as the community grows. Each entry is the
    # name of a directory under skills-dir that ends with /SKILL.md.
    "aerospace-safety", "agent-browser", "agi-heuristic", "ai-agents-architect",
    "ai-architect", "ai-video-creator", "akashic-root", "algorithmic-art",
    "api-contract-guardian", "api-design-principles", "app-builder",
    "architecture-decision-records", "bio-synthetic", "brainstorming",
    "brand-guidelines", "canvas-design", "change-safety-engineer",
    "changelog-generator", "chaos-engineer", "chaos-navigator",
    "civilization-architect", "claude-api", "claude-code-command-creator",
    "cli-mastery", "code-architect", "codebase-cartography",
    "compliance-expert", "concept-materializer", "cryptic-void",
    "cyber-warrior", "data-analysis", "data-migration-surgeon",
    "data-sage", "debugging-hypothesis-lab", "deep-debugging",
    "deep-research-10x", "deep-research-agent", "deep-research-consultant",
    "dependency-upgrade-commander", "devex-toolsmith", "devops-elite",
    "distributed-guru", "distributed-systems-reliability",
    "doc-coauthoring", "docx", "elite-engineering", "episodic-memory",
    "error-handling-patterns", "exploit-foundry", "figma-to-code",
    "financial-singularity", "fintech-architect", "forensic-analyst",
    "frontend-design", "frontend-design-2", "frontend-design-expert",
    "frontend-product-craft", "full-branding-generator", "fullstack-dev-2",
    "html-presentation-generator", "hyper-geometer", "icon-maker",
    "image-generation", "industry-research-report-writer",
    "infra-blackout", "infra-phantom", "innovation-lab",
    "interactive-visualization-architect", "interface-design",
    "internal-comms", "interplanetary-net", "job-hunter",
    "landing-page-builder", "legacy-modernization-strangler",
    "legacy-whisperer", "local-commit-discipline", "logic-transcender",
    "matrix-architect", "mcp-builder", "mcp-ecosystem", "memetic-overlord",
    "mini-coder-max", "minimax-crypto-trading", "minimax-docx",
    "minimax-pdf", "minimax-xlsx", "multimodal-embedding", "n8n",
    "nano-banana-pro", "neural-lace-hijacker", "nexus-orchestrator",
    "observability-engineer", "omniverse-debugger", "openclaw-assistant",
    "pdf", "performance-engineer", "performance-forensics",
    "pptx", "pptx-generator", "prd-assistant", "probability-bender",
    "product-strategist", "professional_excellence", "qa-engine",
    "quantum-cryptographer", "rag-memory", "reality-bender",
    "release-captain", "research-paper-generator", "saas-idea-generator",
    "satellite-constellation-root", "secure-by-design-review",
    "security-overseer", "self-builder", "self-evolution",
    "self-improving-agent", "seo-geo-optimization-expert",
    "shadow-net-architect", "short-video-script", "skill-creator",
    "slack-gif-creator", "social-engineer-prime", "social-media-trend-search",
    "spec-to-shippable-plan", "sre-commander", "superpower-10x",
    "swarm-orchestration", "system-sentinel", "systematic-debugging",
    "tech-debt-radar", "technical-writing-principal", "temporal-mechanic",
    "test-strategy-master", "theme-factory", "ui-ux-designer",
    "ui-ux-pro-max", "ui-virtuoso", "ux-scientist",
    "vercel-react-best-practices", "video-motion-analysis",
    "visual-content-generator", "void-nullifier", "web-app-builder",
    "web-artifacts-builder", "web-scraper", "webapp-testing",
    "world-class-agent-os", "xlsx", "youtube-watcher", "zenith-leader",
)


def detect_and_repair(path: Path, dry_run: bool) -> Tuple[str, str]:
    """Return (status, info). Status is one of: fixed, ok-already, missing,
    unknown-shape, io-error."""
    if not path.exists():
        return ("missing", "")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return ("io-error", str(exc))

    lines = text.split("\n")
    # Shape A — already valid YAML frontmatter.
    if lines and lines[0].strip() == "---":
        return ("ok-already", "")

    # Shape B — legacy `# Skill:` header followed by name: / description:.
    if not lines or not lines[0].startswith("# Skill:"):
        return ("unknown-shape", lines[0][:60] if lines else "<empty>")

    title = lines[0].split("# Skill:", 1)[1].strip()
    name_line = next((l for l in lines[1:6] if l.startswith("name:")), None)
    desc_line = next((l for l in lines[1:6] if l.startswith("description:")), None)
    if not name_line or not desc_line:
        return ("unknown-shape", "missing name: or description: in lines 1-5")
    fm_name = name_line.split(":", 1)[1].strip()
    fm_desc = desc_line.split(":", 1)[1].strip()

    # Drop the duplicated name: / description: lines once we inject FM.
    skip_indices = set()
    for i, l in enumerate(lines[:6]):
        if l.startswith("name:") or l.startswith("description:"):
            skip_indices.add(i)

    body = "\n".join(l for i, l in enumerate(lines) if i not in skip_indices)
    new_text = (
        "---\n"
        f"name: {fm_name}\n"
        f"description: {fm_desc}\n"
        "---\n\n"
        f"# Skill: {title}\n\n"
        f"{body.lstrip()}"
    )
    if dry_run:
        return ("would-fix", new_text[:120].replace("\n", " | "))
    try:
        fd, tmp = tempfile.mkstemp(prefix=".skill-fm-", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(new_text)
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except OSError as exc:
        return ("io-error", str(exc))
    return ("fixed", fm_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry", action="store_true",
                        help="audit only, do not modify files")
    parser.add_argument("--skills-dir", type=Path, default=DEFAULT_DIR,
                        help=f"skills root (default: {DEFAULT_DIR})")
    parser.add_argument("--target", action="append", default=None,
                        help="restrict audit to specific skill names "
                             "(repeatable). Defaults to the full set "
                             "shipped with this skill.")
    args = parser.parse_args()

    skills_dir: Path = args.skills_dir.expanduser()
    targets = args.target if args.target else DEFAULT_TARGETS

    stats = {"fixed": 0, "ok-already": 0, "would-fix": 0,
             "missing": 0, "unknown-shape": 0, "io-error": 0}
    for name in targets:
        path = skills_dir / name / "SKILL.md"
        status, info = detect_and_repair(path, dry_run=args.dry)
        stats[status] = stats.get(status, 0) + 1
        line = f"{name}: {status}"
        if info:
            line += f"  {info}"
        print(line)
    print()
    print("STATS:", {k: v for k, v in stats.items() if v})
    return 0


if __name__ == "__main__":
    sys.exit(main())
