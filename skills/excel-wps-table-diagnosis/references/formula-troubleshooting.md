# Formula Troubleshooting Reference

> Guide for auditing, diagnosing, and fixing broken Excel/WPS formulas.

## Formula Extraction from XLSX

```python
import zipfile, re

def extract_all_formulas(xlsx_path):
    """Extract all formulas from an xlsx file."""
    formulas = {}
    with zipfile.ZipFile(xlsx_path) as z:
        for name in z.namelist():
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                content = z.read(name).decode("utf-8")
                # Find all formula cells: <f>FORMULA_TEXT</f>
                cells = re.findall(r'<c r="([A-Z]+\d+)"[^>]*>.*?<f[^>]*>([^<]+)</f>', content, re.DOTALL)
                formulas[name] = [(cell, formula) for cell, formula in cells]
    return formulas

def find_broken_formulas(xlsx_path):
    """Find cells with formula errors."""
    errors = {}
    with zipfile.ZipFile(xlsx_path) as z:
        for name in z.namelist():
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                content = z.read(name).decode("utf-8")
                # Find error values: <v>#REF!</v>
                error_cells = re.findall(r'<c r="([A-Z]+\d+)"[^>]*>.*?<v>(#[A-Z]+[?!])</v>', content, re.DOTALL)
                if error_cells:
                    errors[name] = error_cells
    return errors
```

## Common Formula Errors

### `#REF!` — Invalid Reference
**Cause**: A column or row referenced was deleted.

```excel
# Broken: =VLOOKUP(A1, Sheet2!B:D, 3, FALSE)
# Fixed:  =VLOOKUP(A1, Sheet2!A:D, 4, FALSE)   -- adjusted column index
# Or:     Use INDEX/MATCH which doesn't break on insertion/deletion
```

### `#VALUE!` — Wrong Data Type
**Cause**: Formula expects a number/text but received the wrong type.

```excel
# Broken: =SUM(A1:A10)  where A5 contains "N/A" text
# Fixed:  =SUMIF(A1:A10,">0")  -- ignores text
# Or:     =AGGREGATE(9,6,A1:A10)  -- ignores errors
```

### `#NAME?` — Unrecognized Function
**Cause**: Function not supported in WPS/Excel version, or typo.

```excel
# XLOOKUP only in Excel 365 / WPS newer versions
# Use VLOOKUP or INDEX/MATCH instead for compatibility
= INDEX(B:B, MATCH(A1, A:A, 0))   -- equivalent to XLOOKUP
```

### `#DIV/0!` — Division by Zero
**Cause**: Denominator is zero or empty.

```excel
# Broken: =A1/B1
# Fixed:  =IFERROR(A1/B1, 0)        -- show 0 when dividing by zero
# Or:     =IF(B1=0, "N/A", A1/B1)  -- explicit message
```

### `#N/A` — Lookup Not Found
**Cause**: VLOOKUP/MATCH found no match.

```excel
# Broken: =VLOOKUP(A1, B:C, 2, FALSE)
# Fixed:  =IFERROR(VLOOKUP(A1, B:C, 2, FALSE), "Not found")
```

### `#NULL!` — Invalid Range
**Cause**: Missing colon or comma in range reference.

```excel
# Broken: =SUM(A1 B1)   -- missing operator
# Fixed:  =SUM(A1:B1)   -- proper range
```

### `#NUM!` — Invalid Numeric Value
**Cause**: Numeric result too large/small, or invalid argument to function.

```excel
# IRR fails when no reasonable rate exists
=IFERROR(IRR(CashFlows), "Cannot compute")
```

## Circular Reference Detection

Excel's Formula → Trace Precedents/Dependents shows circular refs visually.
In XML, a circular reference appears when a cell references itself directly or through a chain.

```python
def find_circular_refs(xlsx_path):
    """Detect potential circular references by building dependency graph."""
    import zipfile, re, networkx as nx

    formulas = extract_all_formulas(xlsx_path)

    G = nx.DiGraph()
    for sheet, cells in formulas.items():
        for cell_ref, formula in cells:
            # Extract referenced cells from formula
            refs = re.findall(r'([A-Z]+[0-9]+)', formula)
            for ref in refs:
                G.add_edge(ref, cell_ref)

    # Find cycles
    try:
        cycles = list(nx.simple_cycles(G))
        return cycles
    except:
        return []
```

## Formula Pattern Reference

### VLOOKUP Best Practices
```excel
=VLOOKUP(lookup_value, $A$1:$D$100, 3, FALSE)
       ^ Always absolute refs for table range
                                    ^ Always FALSE for exact match
```

### SUMIF / COUNTIF
```excel
=SUMIF(A:A, "Active", B:B)           -- sum B where A = "Active"
=COUNTIF(A:A, ">100")               -- count A values > 100
=SUMIFS(C:C, A:A, "Region1", B:B, ">1000")  -- multi-criteria
```

### IFERROR Wrapper Pattern
```excel
=IFERROR(your_formula, fallback_value)
-- Always wrap: VLOOKUP, INDEX/MATCH, IRR, RATE, XIRR
```

### Array Formulas (Ctrl+Shift+Enter)
```excel
{=INDEX(B:B, MATCH(MAX(C:C), C:C, 0))}  -- find row of max value, return B
```

## Excel vs WPS Compatibility

| Function | Excel | WPS |
|----------|-------|-----|
| XLOOKUP | 365+ only | Newer versions only |
| LET | 365+ | Not supported |
| FILTER | 365+ | Not supported |
| IFS | 2019+ | Supported |
| SWITCH | 2019+ | Supported |
| TEXTJOIN | 2019+ | Supported |

**Rule**: Use `IFERROR(VLOOKUP(...), IFERROR(INDEX/MATCH(...), "not found"))` pattern for maximum compatibility.

## Formula Audit Workflow

1. Extract all formulas with `extract_all_formulas()`
2. Find error cells with `find_broken_formulas()`
3. Categorize by error type (#REF!, #VALUE!, etc.)
4. For each broken formula:
   - Identify what it was trying to do
   - Determine if source data was deleted/moved
   - Fix formula and verify with IFERROR
5. After fixes, run `formula_check.py` from minimax-xlsx to verify
