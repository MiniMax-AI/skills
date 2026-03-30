# Example: Table Diagnosis

## Input

Headers:

- Order ID
- Customer ID
- Order Date
- Amount
- Status

Sample rows:

- 1001, C001, 2026/03/01, 89.5, Paid
- 1002, C001, 03-02-2026, 120, paid
- 1003, , 2026.03.05, 45, Pending
- 1003, C004, 2026/03/05, 45, Pending

User request:

`Please inspect this table and tell me what I should clean first.`

## Expected Response Shape

### Diagnosis

- `Order Date` uses mixed date formats
- `Customer ID` has blank values
- `Order ID` contains duplicates
- `Status` is inconsistent because `Paid` and `paid` should likely be standardized

### Recommendation

- standardize `Status` first
- fix blank `Customer ID` values if possible
- normalize `Order Date` into one format
- investigate duplicate `Order ID` before summarizing data

### Compatibility

- prefer simple cleanup formulas and helper columns
- avoid depending on newer dynamic-array functions for this workflow

