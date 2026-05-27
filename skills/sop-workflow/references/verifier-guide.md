# Verifier Guide

## How Verifiers Work

A verifier is an LLM call that evaluates worker output against the task specification. The SOP workflow supports two verification stages:

1. **Stage 1: spec-compliance** — Does the output implement the spec exactly?
2. **Stage 2: code_quality** — Is the code readable, well-structured, and robust?

Evidence results (executed shell commands) are injected into both stages as `=== EVIDENCE RESULTS ===` in the verifier prompt.

## Built-in Verifier Types

| Type | Purpose | Score Threshold | Notes |
|------|---------|-----------------|-------|
| `spec-compliance` | Spec compliance | 3.0 | Stage 1 verifier |
| `code_quality` | Code quality | 3.0 | Stage 2 verifier |
| `security` | Security audit | 4.0 | Single-stage |
| `functional` | Functional correctness | 4.0 | Single-stage |
| `performance` | Performance | 3.0 | Single-stage |
| `comprehensive` | Overall review | 3.8 | Single-stage |

## Verdict Format

Verifiers return a JSON verdict:

```json
{
  "verdict": "PASS",
  "score": 5,
  "summary": "All requirements met",
  "issues": [
    {
      "severity": "high",
      "description": "Missing error handling for null input"
    }
  ]
}
```

**Score scale**: 1-5 (5 = perfect, 1 = completely wrong)

**Verdict values**:
- `PASS`: score >= threshold
- `FAIL`: score < threshold
- `NEEDS_IMPROVEMENT`: passes through without override (treated as FAIL for threshold)

## JSON Parsing Robustness

The verifier parser handles multiple formats:

```javascript
// Full JSON object
{ "verdict": "PASS", "score": 5, "summary": "ok" }

// overall_score field
{ "overall_score": 4.0, "summary": "acceptable" }

// Code fence
```json
{ "verdict": "PASS", "score": 4.5 }
```

```javascript
// Bare quoted fields (robust field extraction)
"verdict": "PASS", "score": 4.5, "summary": "looks good"

// Qualitative verdicts (natural language)
"The implementation looks good and meets all requirements."  // → PASS, score 4.0
"This needs work. Several issues remain."                     // → FAIL, score 2.5
"Excellent work! All criteria met."                          // → PASS, score 4.5
"The solution was rejected due to security issues."           // → FAIL, score 2.0
```

## Evidence Results in Verifier Prompt

When worker output contains ` ```bash ` code blocks, they are executed before the verifier runs. The results appear in the verifier prompt as:

```
=== EVIDENCE RESULTS ===

[PASS] Command: npm test
Output:
✓ 3 tests passed

[FAIL] Command: npm run lint
Output:
SyntaxError: Unexpected token
```

The verifier uses this to assess functional correctness — tests passing influences the score positively.

## Custom Verifiers

You can define custom verifiers in the manifest:

```yaml
config:
  verifiers:
    my-custom-check:
      type: "llm"
      prompt: |
        Review the code for:
        1. Consistency with company coding standards
        2. Proper error messages
        3. Logging statements
      threshold: 3.5
```

## Writing Good Spec Descriptions

The spec description drives the `spec-compliance` verifier. Good specs are:

1. **Complete**: cover all input/output cases
2. **Unambiguous**: use concrete examples
3. **Checkable**: can be verified automatically or by an LLM

## Verdict Interpretation

| Score | Meaning |
|-------|---------|
| 5.0 | Perfect — exceeds expectations |
| 4.0–4.9 | Good — meets all requirements |
| 3.0–3.9 | Acceptable — minor issues |
| 2.0–2.9 | Needs work — significant issues |
| 1.0–1.9 | Poor — major gaps |

Issues with `severity: "high"` must be fixed in adversarial mode. `medium` and `low` issues are noted but don't block.
