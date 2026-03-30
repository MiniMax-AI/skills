# Example: Approval Flow

## Scenario

The user provides a small customer table and asks what should be cleaned first.

Headers:

- Customer ID
- Name
- Phone
- Status

Sample rows:

- 001, Alice, 138 0013 8000, active
- 002, Bob, 13800138001, Active
- 002, Bob, 13800138001, active
- 003, Carol, , inactive

## Phase 1: Diagnose And Recommend

Expected shape:

- explain that `Customer ID` should stay as text
- point out mixed phone formatting
- point out inconsistent `Status` casing
- flag the duplicate `Customer ID`
- suggest helper columns and a cleanup order
- pause before execution

Example pause:

`I have not modified anything yet. If you want, I can continue with the exact helper-column setup and the spreadsheet steps.`

## Phase 2: Execute After Approval

Once the user agrees, the response should move straight into execution.

Expected shape:

- specify which helper columns to add
- give the exact formulas
- explain where to place them
- explain fill-down and cleanup steps
- avoid repeating the same diagnosis unless needed for clarity

Example execution elements:

- `E1: Clean Phone`
- `F1: Clean Status`
- `G1: Dedupe Key`
- `H1: Duplicate?`

- `E2: =SUBSTITUTE(SUBSTITUTE(TRIM(C2),CHAR(160),\"\"),\" \",\"\")`
- `F2: =LOWER(TRIM(D2))`
- `G2: =A2&\"|\"&B2&\"|\"&E2`
- `H2: =IF(COUNTIF($G:$G,G2)>1,\"Duplicate\",\"Keep\")`

## Purpose

This example exists to show the intended behavior of the repository:

1. diagnose first
2. pause before direct spreadsheet work
3. continue immediately once the user approves
