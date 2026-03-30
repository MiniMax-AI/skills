# Use Cases

## 1. Cleanup Before Analysis

Use the project to inspect a table before writing formulas.

This is usually the least exciting step and also the one that prevents the most avoidable trouble.

Typical signals:

- blank values in key columns
- inconsistent date formats
- duplicate identifiers
- status fields with inconsistent capitalization

## 2. Matching Across Sheets

Use the project when two sheets need to be matched by a shared field such as:

- customer ID
- employee ID
- order number
- product code

The goal is to choose a reliable lookup workflow that still works in Excel and WPS.

If the key column is messy, that problem should be handled first instead of hoping the lookup will be forgiving.

## 3. Text Cleanup

Use the project to normalize columns that contain:

- extra spaces
- hidden separators
- mixed capitalization
- text fragments that should be split or extracted

This is where helper columns usually age better than one heroic formula.

## 4. Summarization

Use the project when the user needs to:

- count records by status or department
- summarize sales or amounts
- classify rows by conditions
- prepare a table for a pivot workflow

The useful question here is often not just how to summarize the table, but whether the table is even ready to be summarized.

## 5. Formula Troubleshooting

Use the project when the spreadsheet already has formulas, but they return:

- missing matches
- obvious reference mistakes
- unstable behavior after copy-down
- errors caused by dirty source columns

Sometimes the formula is wrong. Sometimes the table is wrong. It helps to separate those two problems early.
