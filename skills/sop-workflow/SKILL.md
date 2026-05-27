---
name: sop-workflow
description: >
  Use this skill when you need to run structured multi-task agent workflows with
  adversarial verification and parallel execution. Triggers on: "run a workflow",
  "create an SOP", "multi-agent pipeline", "adversarial verification", "parallel tasks",
  "wave execution", "task pipeline", "evidence-based review", "agent SOP".
  This skill implements a cross-platform Agent SOP execution system combining
  Superpowers engineering norms (evidence-before-claims, two-stage review) with
  Mavis adversarial verification (verifier FAIL → worker fixes → re-review).
  It supports: DAG-based parallel task waves, atomic state persistence with crash recovery,
  exponential backoff retries, wave-level cancellation via AbortController, and
  evidence command injection into verifier prompts. Powered by MiniMax-M1 with
  recommended inference parameters (temperature=1.0, top_p=0.95, max_tokens=128K).
  Do NOT load this for simple single-task requests — use it when the user explicitly
  requests a multi-step, multi-agent, or workflow-driven task.
license: MIT
metadata:
  version: "1.0"
  category: agent-workflow
  sources:
    - https://github.com/MiniMax-AI/skills
---

# SOP Workflow Skill

> **Code as Law** — execution flow is hardcoded in JS; the model acts only within agent() nodes.

## Overview

SOP Workflow is a cross-platform agent workflow execution system that combines:

- **Superpowers engineering norms**: evidence-before-claims, two-stage review (spec compliance → code quality)
- **Mavis adversarial verification**: verifier FAIL → worker fixes → re-review loop
- **MiniMax-M1 recommended parameters**: temperature=1.0, top_p=0.95, max_tokens=128K

The core principle: **flow must not drift** — all execution paths are hardcoded in JS; the model cannot skip verification steps.

## Quick Start

### 1. Create a Manifest

```yaml
manifest_version: "1"
name: "my-feature"
config:
  model: "MiniMax/MiniMax"
  adversarial_mode: true
  verifier_max_retries: 2

phases:
  build:
    tasks:
      - id: "task-1"
        title: "Implement feature"
        description: "Write a Node.js function that..."
        agent_role: "worker"
        verifier: "spec-compliance"
```

### 2. Run

```bash
SOP_PLATFORM=minimax SOP_LLM_MODEL=MiniMax-M2.7-highspeed \
  MAVIS_ACCESS_TOKEN=your_token \
  node engines/workflow-engine.js run my-sop.yaml
```

### 3. Test

```bash
npm test   # 42 unit tests
```

## Architecture

```
sop-workflow/
├── SKILL.md                  # This file
├── references/
│   ├── manifest-format.md     # Full manifest YAML reference
│   └── verifier-guide.md     # Verifier types and thresholds
├── engines/
│   ├── workflow-engine.js     # Core engine (~2000 lines)
│   └── test-engine.js         # 42 unit tests
└── scripts/
    └── bootstrap.sh          # Quick-start manifest generator
```

## Parallel Execution (Wave-based DAG)

Tasks in the same phase execute in waves based on their dependency graph:

- **Wave 0**: tasks with no dependencies (immediate parallel)
- **Wave N**: tasks whose dependencies are all in Wave N-1 (parallel)
- **Cross-phase**: always sequential
- **External dependencies**: tasks depending on other phases are treated as satisfied

```yaml
tasks:
  - id: "a"                         # Wave 0
  - id: "b"; depends_on: ["a"]     # Wave 1 (|| with c)
  - id: "c"; depends_on: ["a"]     # Wave 1
  - id: "d"; depends_on: ["b","c"] # Wave 2
```

## Two-Stage Review (Core Feature)

Every task is verified in two stages:

| Stage | Verifier | Checks |
|-------|----------|--------|
| 1 | `spec-compliance` | Does output implement the spec exactly? |
| 2 | `code_quality` | Readability, error handling, test coverage |

Stage 1 FAIL → no Stage 2 → adversarial retry.

## Adversarial Loop

```
Worker output → Verifier → FAIL → Worker fixes → Verifier re-reviews
                                                   ↓
                                              PASS → next task
```

- `verifier_max_retries: 2` (default): up to 2 fix rounds
- `adversarial_mode: true`: FAIL stops the entire workflow
- Verifier FAIL includes issues JSON + evidence output in the feedback prompt

## Wave-Level Cancellation

When any task in a wave fails (adversarial mode):

1. AbortController signals all sibling tasks in the wave
2. In-flight MiniMax API requests are aborted immediately
3. Cancelled tasks are marked `failed`
4. Subsequent waves are not started

## Evidence Before Claims

Shell commands embedded in worker output are auto-executed before verification:

```
Worker output:  ```bash npm test ```
→ Auto-executes: npm test
→ Result injected into verifier prompt → VERIFIED
```

- Commands run in parallel (non-blocking)
- Non-zero exit code → evidence FAIL → affects verifier score
- Timeout: 30s per command (configurable)

## Atomic State Persistence

State saves use write-then-rename (POSIX atomic):

```
writeFileSync(tmp) → renameSync(tmp, final)
```

Crash recovery: reads `.sop-workflow-state.json` and resumes from the last saved phase + task.

## Verifier Types

| Verifier | Purpose | Threshold |
|----------|---------|-----------|
| `spec-compliance` | Spec compliance | 3.0 |
| `code_quality` | Code quality | 3.0 |
| `security` | Security audit | 4.0 |
| `functional` | Functional correctness | 4.0 |
| `performance` | Performance | 3.0 |
| `comprehensive` | Overall review | 3.8 |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SOP_PLATFORM` | `opencode` | Target platform: `minimax` (cloud) |
| `SOP_LLM_MODEL` | `MiniMax-M2.7-highspeed` | Model name |
| `SOP_MAX_OUTPUT_TOKENS` | `131072` | Output token cap (128K default) |
| `SOP_TOKEN_BUDGET` | `100000` | Token budget |
| `MAVIS_ACCESS_TOKEN` | (required) | MiniMax API JWT |

## Token Tracking

MiniMax API's `output_tokens` does **not** include thinking blocks. An estimate is used: `output_tokens + (thinking_chars / 4)`. The 80% warning threshold is based on this estimate.

## Unit Tests

42 tests covering:

- Manifest parsing (valid/invalid YAML)
- State persistence (including corrupted JSON recovery)
- Token tracking (including thinking block estimation)
- Two-stage review logic (PASS/FAIL/NEEDS_IMPROVEMENT)
- Code block extraction (single/multi)
- `_executeTool` (all tool types)
- `BUILTIN_TOOLS` export completeness
- Wave grouping algorithm (no deps, chain, external, diamond)
- End-to-end parallel execution (4-task diamond dependency)
- Adversarial mode task failure stop
- Circular dependency detection
- Token threshold warning
- Task skip on resume
- `_writeTaskContext` context file writing
- `_retryWithBackoff` exponential backoff
- Evidence commands parallel execution (async Promise.all)
- Evidence results injected into verifier prompt (first-pass)
- Verifier qualitative verdict + bare JSON field parsing
