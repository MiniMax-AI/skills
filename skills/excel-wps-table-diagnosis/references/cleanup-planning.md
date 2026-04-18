# Cleanup Planning Reference

> Guide for planning and executing spreadsheet cleanup operations safely.

## Cleanup Priority Order

1. **High severity first**: Blanks → merged cells → type inconsistencies → duplicates → whitespace
2. **Non-destructive first**: Add correction columns rather than overwriting originals
3. **Verify after each step**: Re-read file after each change to confirm expected state

## Blank Row Removal

**When to remove**: Blank rows between data break VLOOKUP, pivot tables, and AutoFilter.

**Safe removal approach**:
```python
import pandas as pd

df = pd.read_excel("input.xlsx", sheet_name="Sales")
# Keep only rows with at least one non-null value
df_clean = df.dropna(how='all')
# Or keep rows where key column is not null
df_clean = df[df['ID'].notna()]  # adjust 'ID' to actual key column
```

**⚠️ Before removing blanks, check**:
- Are blanks intentional separators (section dividers)?
- Does any formula reference these row numbers?
- Will removing them shift downstream SUM ranges?

## Duplicate Handling

```python
# Find exact duplicates
dups = df[df.duplicated(keep=False)]
print(f"Duplicate rows: {len(dups)}")

# Keep first occurrence, remove rest
df_deduped = df.drop_duplicates(keep='first')

# Remove duplicates based on specific columns only
df_deduped = df.drop_duplicates(subset=['Name', 'Email'], keep='first')
```

## Type Standardization

### Text to Number
```python
def text_to_number(series):
    """Convert text numbers to actual numbers."""
    def try_convert(val):
        if isinstance(val, str):
            cleaned = val.strip().replace(',', '').replace('$', '').replace('¥', '').replace('€', '').replace('%', '')
            try:
                return float(cleaned) if '.' in cleaned else int(cleaned)
            except ValueError:
                return val
        return val
    return series.apply(try_convert)

df['Revenue'] = text_to_number(df['Revenue'])
```

### Number to Text (for IDs/codes)
```python
df['ProductCode'] = df['ProductCode'].astype(str).str.strip()
```

### Date Standardization
```python
df['OrderDate'] = pd.to_datetime(df['OrderDate'], errors='coerce')
# If many dates are text with mixed formats:
df['OrderDate'] = pd.to_datetime(df['OrderDate'], format='%Y/%m/%d', errors='coerce')
```

## Whitespace Cleanup

```python
# Trim leading/trailing whitespace in all text columns
str_cols = df.select_dtypes(include='object').columns
df[str_cols] = df[str_cols].apply(lambda x: x.str.strip() if hasattr(x, 'str') else x)

# Normalize internal multiple spaces to single space
df[str_cols] = df[str_cols].apply(
    lambda x: x.str.replace(r'\s+', ' ', regex=True) if hasattr(x, 'str') else x
)
```

## Merged Cell Handling

**Merged cells cause misalignment in pandas read_excel.**

```python
# When reading a file with merged cells:
df = pd.read_excel("input.xlsx", header=None)  # raw read, no header parsing
# Manually set header from row 0
# Manually fill merged cell values down
```

**In XML (for direct editing)**, merged cells look like:
```xml
<mergeCells count="2">
  <mergeCell ref="B2:D2"/>  <!-- B2 merged with C2 and D2 -->
</mergeCells>
```

**Before editing**: Unmerge all cells first, then re-merge if needed after cleanup.

## Column Operations

### Add a Cleanup Status Column
```python
# Add a column tracking what was changed (useful for audit)
df['__cleanup_notes'] = ''
df.loc[df['Revenue'].apply(lambda x: isinstance(x, str)), '__cleanup_notes'] += 'text-to-number;'
df.loc[df['Name'].str.contains(r'^\s|\s$', regex=True, na=False), '__cleanup_notes'] += 'trim-whitespace;'
```

### Reorder Columns
```python
# Put key columns first, cleanup-notes last
cols = [c for c in df.columns if not c.startswith('__')]
cols += [c for c in df.columns if c.startswith('__')]
df = df[cols]
```

## Lookup Key Preparation

**Before using VLOOKUP/INDEX-MATCH, ensure keys are clean:**

```python
# VLOOKUP-ready key requirements:
# 1. No leading/trailing spaces
# 2. Consistent case (or UPPER() applied)
# 3. No hidden characters
# 4. No mixed types (all text or all number)

df['LookupKey'] = df['LookupKey'].astype(str).str.strip().str.upper()
# Or for numeric keys:
df['LookupKey'] = pd.to_numeric(df['LookupKey'], errors='coerce')
```

## Approval Workflow

After diagnosis, present cleanup plan with these categories:

```
## Proposed Cleanup Plan

### High Priority (fix before any analysis)
1. Remove 12 blank rows in Sheet1
2. Unmerge 3 cell ranges in Sheet2
3. Convert column C from text to number (47 cells)

### Medium Priority (fix for correct results)
4. Remove 5 duplicate rows in Sheet1
5. Trim whitespace in columns B, D, F (Sheet1)
6. Standardize date format in column G (Sheet1)

### Low Priority (nice to have)
7. Add data validation dropdowns to column A
8. Freeze top row (Sheet1)

### Estimated Impact
- Rows after cleanup: ~{n} (from ~{m})
- Formulas that may be affected: 3 (will verify after changes)
```

**User response to approval:**
- `APPROVE` → proceed with all items
- `APPROVE, skip 2 and 5` → selective approval
- `APPROVE 1-3 only` → partial approval
- Any other response → ask for clarification
