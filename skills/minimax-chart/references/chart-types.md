# Chart Type Selection Guide

How to pick the right chart for your data.

## Decision Tree

```
What are you showing?
├── Comparison across categories
│   ├── Few categories (< 7) → Bar chart
│   ├── Many categories (7+) → Horizontal bar chart
│   └── Parts of a whole → Pie / donut chart (max 6 slices)
├── Change over time
│   ├── Single metric → Line chart
│   ├── Multiple metrics → Multi-line chart
│   └── Cumulative → Area chart
├── Relationship between variables
│   ├── 2 numeric variables → Scatter plot
│   └── With trend → Scatter + trend line
├── Distribution
│   ├── Single variable → Histogram
│   └── Across categories → Box plot
└── Intensity / density
    └── 2D grid of values → Heatmap
```

## Chart Type Reference

| Chart | Best for | Avoid when |
|-------|----------|------------|
| **Bar** | Comparing categories | More than 15 categories |
| **Line** | Trends over time | Unordered categories |
| **Scatter** | Correlation between 2 variables | Categorical data |
| **Pie** | Parts of a whole | More than 6 slices |
| **Histogram** | Value distribution | Categorical data |
| **Heatmap** | Intensity across 2 dimensions | Few data points |
| **Grouped bar** | Comparing groups within categories | Too many groups (>4) |
| **Stacked bar** | Composition within categories | When individual values matter more than totals |

## Style Guidelines

### Colors
- Use consistent colors for the same data series across multiple charts
- Avoid red/green together (color blindness)
- Use sequential colormaps (e.g., `YlOrRd`) for heatmaps
- Use distinct colors for categorical data

### Labels
- Always label both axes
- Include units in axis labels: "Revenue ($K)" not just "Revenue"
- Use title case for titles, sentence case for labels
- Rotate long x-axis labels 45 degrees

### Sizing
- Default: 10x6 inches at 150 DPI (1500x900px)
- Presentations: 12x7 inches at 200 DPI
- Print: 8x5 inches at 300 DPI
- Thumbnails: 6x4 inches at 100 DPI
