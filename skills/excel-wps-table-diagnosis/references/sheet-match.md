# Example: Sheet Match

## Input

Sheet A:

- Customer ID
- Name
- Region

Sheet B:

- Customer ID
- Last Purchase Date
- Total Amount

User request:

`I need to match Sheet A and Sheet B by customer ID in WPS.`

## Expected Response Shape

### Diagnosis

- `Customer ID` is the most likely key column
- matching should be done only after checking for duplicate IDs

### Recommendation

- use a lookup formula based on `Customer ID`
- if broad compatibility matters, prefer `INDEX + MATCH`
- if the environment supports it, a simpler lookup function may also be suggested

### Compatibility

- provide a WPS-friendly formula first
- mention a newer Excel-only alternative only as a secondary option

