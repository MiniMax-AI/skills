# Contributing to MiniMax Skills

Thank you for your interest in contributing! This document covers PR requirements, skill structure specifications, and development guidelines.

## Pull Request Requirements

### Title Format

Use [Conventional Commits](https://www.conventionalcommits.org/) style:

```
feat(<skill-name>): add new skill for X
fix(<skill-name>): fix YAML frontmatter parsing error
docs: update README skill table
chore: add CI workflow
```

Common prefixes: `feat` (new skill or feature), `fix` (bug fix), `docs` (documentation only), `refactor` (restructure without behavior change), `chore` (tooling, CI, config).

### Scope

**One PR, one purpose.** Each PR should do exactly one of:

- Add a new skill
- Fix a bug in an existing skill
- Improve an existing skill

Do not bundle unrelated changes together.

### PR Description

Every PR must include:

1. **What** — what you added or changed
2. **Why** — the motivation or use case

## Skill Structure

### Directory Layout

```
skills/<skill-name>/
├── SKILL.md                 # Required — entry point with YAML frontmatter
├── references/              # Optional — detailed reference docs
│   └── *.md
└── scripts/                 # Optional — helper scripts
    ├── *.py
    └── requirements.txt     # Required if scripts/ exists
```

- The directory name is the skill identifier. Use lowercase `kebab-case` (e.g., `gif-sticker-maker`).
- `SKILL.md` is the only required file. All other files and directories are optional.

### SKILL.md Frontmatter

```yaml
---
name: my-skill                    # Required — must match directory name
description: >                    # Required — what this skill does and when to trigger it
  One-paragraph description. Include trigger conditions so the agent
  knows when to activate this skill (e.g., "Use when the user asks to
  create, edit, or format Excel files").
license: MIT                      # Recommended — defaults to MIT if omitted
metadata:                         # Recommended
  version: "1.0"
  category: productivity           # e.g., frontend, mobile, productivity, creative
  sources:
    - Relevant documentation or standards
---
```

**Required fields:** `name`, `description`

- `name` must exactly match the directory name
- `description` must clearly state trigger conditions — this is what the agent uses to decide whether to load your skill

**Recommended fields:** `license`, `metadata` (version, category, sources)

### No Hardcoded Secrets

**Never hardcode API keys, tokens, or credentials in any file.**

If your skill involves calling an external API, instruct the agent to read credentials from environment variables. Follow the pattern established by existing skills:

```python
API_KEY = os.getenv("MINIMAX_API_KEY")
if not API_KEY:
    raise SystemExit("ERROR: MINIMAX_API_KEY is not set.\n  export MINIMAX_API_KEY='your-key'")
```

Your `SKILL.md` should document the required environment variables as a prerequisite. See `frontend-dev/references/env-setup.md` for a good example.

### README Sync

When adding a new skill, update both `README.md` and `README_zh.md` to include your skill in the skill table. Community-submitted skills should set the Source column to `Community`.

## Guidelines

The following are not hard blockers, but PRs that follow these guidelines will be reviewed and merged faster.

### 1. Skill Scope — Avoid Overlap

Before creating a new skill, check existing skills for functional overlap. If your feature could be an extension of an existing skill, prefer extending over creating a new one.

In your PR description, briefly explain how your skill differs from related existing skills. For example, if you are adding a voice synthesis skill, clarify how it relates to the TTS capabilities already in `frontend-dev`.

### 2. File Size Awareness

Skills are loaded into the agent's context window. Every token counts.

- Keep individual `.md` files focused and concise
- If a reference document grows very large, split it into logical parts (see `minimax-docx/references/openxml_encyclopedia_part{1,2,3}.md` for an example)
- Avoid embedding large data blobs (base64 images, full API response dumps) directly in Markdown files
- Prefer linking to external resources over inlining lengthy content

### 3. Script Standards

If your skill includes helper scripts (typically in a `scripts/` directory):

- Include a shebang line (e.g., `#!/usr/bin/env python3`)
- Provide a `requirements.txt` listing all dependencies
- Handle errors gracefully — fail with a clear message rather than a raw traceback
- Document script usage in `SKILL.md` or a reference file

### 4. Language and Encoding

- Skill names and file names: ASCII only, `kebab-case`
- SKILL.md content and code should be written in English
- Reference docs are recommended to be in English
- All files must be UTF-8 encoded

## Review Process

You can run the validation script locally to check part of the requirements before submitting:

```bash
python .claude/skills/pr-review/scripts/validate_skills.py
```

You can also use the [pr-review skill](./.claude/skills/pr-review/SKILL.md) to let your AI coding agent assist with the review.

1. Submit your PR following the requirements above
2. At least one maintainer will review
3. Address review feedback
4. Once approved, a maintainer will merge

## Questions?

Open an issue if you have questions about contributing. We're happy to help.
