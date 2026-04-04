# Table Diagnosis Reference

> Detailed guide for diagnosing spreadsheet structure and data quality issues.

## Diagnosis Checklist

Run through these checks systematically for every sheet.

### 1. Structural Checks

- [ ] **Header row**: Is there a proper header on row 1? Are headers unique?
- [ ] **Blank rows**: Any rows where ALL cells are empty?
- [ ] **Merged cells**: Open XML and check `<mergeCells>` — merged cells cause offset issues
- [ ] **Total rows**: Is there a grand-total row that should be excluded from analysis?
- [ ] **Notes/comments**: Hidden notes that affect data interpretation

### 2. Data Quality Checks

```python
import pandas as pd

def full_quality_audit(sheet_df, sheet_name):
    """Comprehensive quality audit for a single sheet."""
    issues = []

    # Blank rows
    blank_mask = sheet_df.isnull().all(axis=1)
    blank_count = blank_mask.sum()
    if blank_count > 0:
        issues.append({
            "type": "blank_rows",
            "severity": "high",
            "count": int(blank_count),
            "rows": [int(i) for i in sheet_df[blank_mask].index]
        })

    # Duplicate rows
    dup_count = sheet_df.duplicated().sum()
    if dup_count > 0:
        issues.append({
            "type": "duplicate_rows",
            "severity": "medium",
            "count": int(dup_count)
        })

    # Column-wise null check
    null_by_col = sheet_df.isnull().sum()
    for col, null_count in null_by_col.items():
        if null_count > 0:
            pct = null_count / len(sheet_df) * 100
            issues.append({
                "type": "null_in_column",
                "severity": "high" if pct > 20 else "medium",
                "column": col,
                "count": int(null_count),
                "percentage": round(pct, 1)
            })

    # Mixed types per column
    for col in sheet_df.columns:
        types = sheet_df[col].apply(lambda x: type(x).__name__).nunique()
        if types > 1:
            type_counts = sheet_df[col].apply(lambda x: type(x).__name__).value_counts().to_dict()
            issues.append({
                "type": "mixed_types",
                "column": col,
                "severity": "medium",
                "types": type_counts
            })

    # Whitespace issues
    str_cols = sheet_df.select_dtypes(include='object').columns
    for col in str_cols:
        has_ws = sheet_df[col].astype(str).str.contains(r'^\s|\s$', regex=True).any()
        if has_ws:
            issues.append({
                "type": "whitespace",
                "column": col,
                "severity": "medium"
            })

    return issues
```

### 3. Type Detection Patterns

```python
# Detect numbers stored as text
def find_text_numbers(series):
    """Find numeric values stored as text."""
    text_mask = series.apply(lambda x: isinstance(x, str))
    text_series = series[text_mask]
    numeric_as_text = text_series.apply(
        lambda x: x.strip().replace(',', '').replace('$', '').replace('¥', '').replace('€', '')
    ).str.match(r'^-?\d+\.?\d*$')
    return series[text_mask][numeric_as_text].index.tolist()

# Detect dates stored as text
def find_text_dates(series):
    """Find date-like strings that should be dates."""
    import re
    date_pattern = re.compile(r'^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}$')
    return series[series.apply(lambda x: bool(date_pattern.match(str(x))) if isinstance(x, str) else False)].index.tolist()
```

### 4. Merged Cell Detection (XML)

```python
import zipfile

def get_merged_cells(xlsx_path, sheet_index=1):
    """Extract merged cell ranges from xlsx XML."""
    with zipfile.ZipFile(xlsx_path) as z:
        sheet_name = f"xl/worksheets/sheet{sheet_index}.xml"
        try:
            content = z.read(sheet_name).decode()
        except KeyError:
            return []

        import re
        merged = re.findall(r'<mergeCell ref="([A-Z]+[0-9]+:[A-Z]+[0-9]+)"', content)
        return merged
```

### 5. Report Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| **High** | Breaks formulas, lookups, or pivot tables | Must fix before any write operation |
| **Medium** | Causes incorrect analysis or display | Fix recommended, but data is usable |
| **Low** | Cosmetic / minor inconsistency | Fix if easy, otherwise note and move on |

### 6. Per-Sheet Summary Template

```
Sheet: {sheet_name}
  Dimensions: {rows}R × {cols}C
  Header: {ok/missing/merged}
  Blanks: {n} rows affected
  Duplicates: {n} rows
  Nulls: {n} cells total ({pct}% of sheet)
  Mixed types: {n} columns
  Whitespace: {n} columns
  Formulas: {n} total, {broken} broken
  Merged cells: {n} ranges

Top issues by severity:
  1. [HIGH] {issue description}
  2. [MED] {issue description}
```
