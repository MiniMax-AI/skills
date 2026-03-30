# Example: Text Cleanup

## Input

Column values:

- ` Alice`
- `Bob  `
- `  Carol`
- `DAVE`
- `eve `

User request:

`This column has extra spaces and inconsistent formatting. How should I clean it?`

## Expected Response Shape

### Diagnosis

- extra leading and trailing spaces
- mixed capitalization

### Recommendation

- trim extra spaces first
- then normalize capitalization if needed
- use helper columns if the cleanup should stay easy to review

### Compatibility

- prefer basic text functions that work in both Excel and WPS
