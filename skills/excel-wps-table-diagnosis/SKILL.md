---
name: excel-wps-table-diagnosis
description: Diagnose spreadsheet structure and recommend practical Excel/WPS-compatible formulas and workflows for cleaning, lookup and matching, summarization, text and date cleanup, and common formula troubleshooting. Use when the user asks what formula to use, how to process a table, how to clean messy columns, how to match sheets, how to make a solution work in both Excel and WPS, or when headers and sample rows should be inspected before deciding what to do next.
---

# Excel/WPS Table Diagnosis

Use this skill when a spreadsheet task should start with the table itself, not with a guess at the formula.

## Core Approach

1. Inspect the input.

- Identify whether the user provided headers, sample rows, CSV content, or only a task description.
- If the structure is unclear, ask for the smallest missing detail that would change the recommendation.

2. Diagnose the table.

- Identify likely column types such as IDs, dates, amounts, names, status fields, phone numbers, or free text.
- Look for blanks, duplicates, mixed formats, unstable lookup keys, and columns that should be cleaned before formulas are applied.

3. Choose the most practical path.

- Prefer simple formulas when they are stable and readable.
- Prefer Excel and WPS compatible approaches over newer functions with weaker compatibility.
- Prefer helper columns when a single long formula would be fragile.
- Recommend built-in spreadsheet tools when they are a better fit than formulas.

4. Present a clear recommendation.

- State what the table appears to contain.
- State what should be done first.
- Recommend the formula or workflow.
- Mention compatibility notes for Excel and WPS.
- Provide a fallback when the preferred formula may not work everywhere.

5. Pause before execution.

- If the next step would directly modify a workbook, add helper columns, rewrite formulas, or otherwise move from diagnosis into execution, ask for confirmation first.
- Once the user agrees, continue with the concrete formulas, helper columns, or execution steps instead of repeating the analysis.
- If the scope is already clear, finish the approved execution step before suggesting extra optional follow-up work.

## Priorities

- Diagnose before suggesting formulas.
- Prefer maintainability over cleverness.
- Treat compatibility as an early constraint.
- Do not force everything into one formula.
- Do not make direct spreadsheet changes without user confirmation.

## Output Shape

Keep the response close to this shape:

### Diagnosis

- what the table likely contains
- what looks inconsistent or risky

### Recommendation

- what to do first
- which formula or method to use

### Execution

- what can be done immediately after approval
- which formulas, helper columns, or spreadsheet steps should be applied

### Compatibility

- whether it should work in Excel
- whether it should work in WPS
- what fallback to use if needed

### Notes

- where to place the formula
- whether helper columns or built-in tools would be easier

## References

- Read `WORKFLOW.md` for the longer working notes.
- Read `docs/use-cases.md` for common task shapes.
- Read `examples/README.md` for example inputs and outputs.
