---
name: excel-wps-table-diagnosis
description: >-
  Diagnose table structure, plan cleanup workflows, and troubleshoot formulas in Excel/WPS spreadsheet files (.xlsx, .xlsm, .csv, .tsv).
  Use when the user asks to audit, inspect, check, diagnose, or analyze the quality and structure of a spreadsheet,
  or when they want a cleanup plan before modifying data. Triggers on 'diagnose', 'audit', 'check quality',
  'find problems', 'table structure', 'data cleanup', 'duplicate', 'blank row', 'inconsistent format',
  or any request to understand issues in a spreadsheet before editing it. This skill does NOT modify files —
  it produces a diagnosis report and pauses for user approval before any write operations.
license: MIT
metadata:
  version: "1.0"
  category: productivity
  sources:
    - ECMA-376 Office Open XML File Formats
    - Microsoft Open XML SDK documentation
---

# Excel/WPS Table Diagnosis Skill

Diagnose spreadsheet problems and produce a cleanup plan. **This skill is read-only — it does not modify files.**
After diagnosis, present findings to the user and await approval before any write operations.

## Diagnosis Workflow

### Step 1 — Structure Discovery

Use `xlsx_reader.py` (from `minimax-xlsx/scripts/`) for initial structure and quality audit:

```bash
python3 SKILL_DIR/../minimax-xlsx/scripts/xlsx_reader.py input.xlsx --quality
python3 SKILL_DIR/../minimax-xlsx/scripts/xlsx_reader.py input.xlsx --json
```

For CSV/TSV files, load directly with pandas:

```python
import pandas as pd
df = pd.read_csv("file.csv")
```

### Step 2 — Deep Diagnosis

After structure discovery, perform targeted analysis using pandas and XML inspection:

**Header and structure analysis:**
```python
import pandas as pd

df = pd.read_excel("input.xlsx", sheet_name=None)  # all sheets
for name, sheet in df.items():
    print(f"Sheet: {name}")
    print(f"  Shape: {sheet.shape}")
    print(f"  Columns: {list(sheet.columns)}")
    print(f"  dtypes:\n{sheet.dtypes}")
    print(f"  Nulls: {sheet.isnull().sum().to_dict()}")
    print(f"  Duplicates: {sheet.duplicated().sum()}")
```

**Data quality issues to flag:**
| Issue | Detection | Impact |
|-------|-----------|--------|
| Blank rows | `sheet[sheet.isnull().all(axis=1)]` | Breaks pivot tables, VLOOKUP |
| Merged cells | Inspect `<mergeCells>` in XML | Misaligns data reading |
| Duplicate headers | `sheet.columns.duplicated()` | Collapses column names |
| Mixed types in column | `sheet.applymap(type).nunique() > 1` | Causes calculation errors |
| Leading/trailing spaces | `sheet.apply(lambda x: x.astype(str).str.strip().ne(x))` | VLOOKUP failures |
| Inconsistent date formats | Detect via `pd.to_datetime(errors='coerce')` | Date calculation failures |
| Numeric stored as text | `pd.to_numeric(errors='coerce')` produces NaN | SUM/AVG ignore text |

**Formula auditing:**
```python
import zipfile, re

with zipfile.ZipFile("input.xlsx") as z:
    for name in z.namelist():
        if name.startswith("xl/worksheets/sheet"):
            content = z.read(name).decode()
            formulas = re.findall(r'<f>([^<]+)</f>', content)
            print(f"{name}: {len(formulas)} formulas")
```

### Step 3 — Produce Diagnosis Report

Format findings as:

```
## Table Diagnosis Report: {filename}

### 1. File Overview
- Format: .xlsx / .xlsm / .csv
- Sheets: {count}
- Dimensions: {rows} rows × {cols} columns

### 2. Data Quality Issues
| # | Sheet | Issue | Rows Affected | Severity |
|---|-------|-------|---------------|----------|
| 1 | Sheet1 | 12 blank rows | rows 15, 28, ... | High |
| 2 | Sheet1 | Column C: mixed text/number | row 4, 9, 17 | Medium |

### 3. Cleanup Plan
1. Remove 12 blank rows (rows 15, 28, ...)
2. Standardize column C: convert text to number (rows 4, 9, 17)
3. Trim whitespace in column B

### 4. Lookup/Matching Workflow Recommendations
- Column A (ID) can serve as VLOOKUP key after deduplication
- Consider INDEX/MATCH instead of VLOOKUP for multi-sheet lookup

### 5. Formula Health Check
- 3 broken formulas detected (see details below)
- 0 circular references found

### 6. User Approval Required
**Proposed actions:**
- Remove 12 blank rows
- Standardize 3 columns (C, D, E) to consistent types
- Trim whitespace in 2 columns (B, F)
- Fix 3 broken formulas

> ⚠️ This report was generated automatically. Review each item before approving changes.
> Reply **APPROVE** to proceed with cleanup, or specify which items to skip.
```

## Lookup and Matching Reference

### VLOOKUP (when to use)
```python
# VLOOKUP: find in leftmost column, return Nth column to the right
= VLOOKUP(lookup_value, table_range, col_index, FALSE)

# Common failure causes:
# 1. Lookup value not in first column
# 2. Table range shifts when copied → use absolute refs: $A$1:$D$100
# 3. Approximate match (TRUE) used instead of exact (FALSE)
```

### INDEX/MATCH (preferred for complex lookups)
```python
= INDEX(return_range, MATCH(lookup_value, lookup_range, 0))
# Works regardless of column position, more flexible than VLOOKUP
```

### XLOOKUP (Excel 365 / WPS newer versions)
```python
= XLOOKUP(lookup_value, lookup_array, return_array, if_not_found)
```

## Formula Troubleshooting Guide

**See `references/formula-troubleshooting.md` for detailed patterns.**

Common formula failures and fixes:

| Error | Cause | Fix |
|-------|-------|-----|
| `#REF!` | Deleted column/row referenced | Update cell references |
| `#VALUE!` | Wrong data type in formula | Convert with `VALUE()`, `TEXT()` |
| `#NAME?` | Unrecognized function | Check Excel vs WPS function names |
| `#DIV/0!` | Division by zero | Wrap with `IFERROR(..., 0)` |
| `#N/A` | Lookup value not found | Verify with `IFERROR(VLOOKUP(...), "not found")` |
| `####` | Column too narrow | Auto-fit column width |
| Circular ref | Cell references itself | Trace precedents with Formulas tab |

## Approval-Based Execution Flow

1. **Diagnose** (this skill) → produces report → user reviews
2. **User replies APPROVE** or lists items to skip
3. **Edit skill activates** → uses `minimax-xlsx` EDIT workflow for modifications
4. **Deliver output file** → verify with `xlsx_reader.py`

**Approval message format:**
```
APPROVE                          # approve all proposed changes
APPROVE, skip item 2 and 3      # partial approval
SKIP cleanup, just fix formulas  # partial approval
```
