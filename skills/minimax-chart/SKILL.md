---
name: minimax-chart
description: |
  Generate publication-ready data visualizations from CSV, JSON, or inline data.
  Use when: creating charts, graphs, plots, data visualizations, infographics,
  turning data into visuals, visualizing CSV files, making bar charts, line charts,
  pie charts, heatmaps, scatter plots.
  Triggers: chart, graph, plot, visualize data, data visualization, bar chart,
  line chart, pie chart, heatmap, scatter plot, CSV to chart.
license: MIT
metadata:
  version: "1.0"
  category: data-tools
  output_format: png/svg/pdf
  sources:
    - matplotlib documentation
    - seaborn documentation
---

# MiniMax Chart

Generate publication-ready charts and data visualizations.

## Prerequisites

Before starting, ensure:

1. **Python venv** is activated with dependencies from [requirements.txt](references/requirements.txt) installed

If matplotlib is not installed, set it up first:
```bash
pip install matplotlib pandas
```

## Workflow

### Step 0: Data Input

Accept data in one of these formats:

1. **CSV file** - `python3 scripts/chart_create.py data.csv -o chart.png`
2. **JSON file** - array of objects or `{labels: [], values: []}` structure
3. **Inline markdown table** - parse from user message
4. **Clipboard / pasted data** - tab-separated or comma-separated text

If the user pastes raw data, save it to a temporary CSV before processing.

### Step 1: Data Analysis

Examine the data to determine:

- **Column types**: numeric, categorical, datetime, text
- **Row count**: affects chart density and readability
- **Relationships**: correlations, time series patterns, distributions

Print a brief summary:
```
Data: 4 columns, 12 rows
  - month (datetime): Jan 2024 - Dec 2024
  - revenue (numeric): range 45K - 120K
  - expenses (numeric): range 30K - 85K
  - category (categorical): 3 unique values
```

### Step 2: Chart Type Selection

**Auto-detect the best chart type based on data shape:**

| Data Pattern | Recommended Chart | Why |
|---|---|---|
| 1 category + 1 numeric | Bar chart | Compare values across categories |
| Datetime + 1-3 numeric | Line chart | Show trends over time |
| 2 numeric columns | Scatter plot | Show correlation |
| 1 category (proportions) | Pie / donut chart | Show parts of a whole |
| Matrix / grid of values | Heatmap | Show intensity across 2 dimensions |
| Multiple groups + numeric | Grouped bar chart | Compare groups side by side |
| Distribution of 1 numeric | Histogram | Show value distribution |
| Category + subcategory + value | Stacked bar chart | Show composition within groups |

Present the recommendation and ask:
> "Based on your data, I recommend a {chart type}. Want to go with that, or prefer a different chart type?"

### Step 3: Style Selection

Offer style presets:

| Style | Description | Best for |
|---|---|---|
| `modern` | Clean, minimal, muted palette | Business reports, presentations |
| `vibrant` | Bold colors, high contrast | Marketing, social media |
| `academic` | Serif fonts, grayscale-friendly | Papers, publications |
| `dark` | Dark background, neon accents | Dashboards, tech content |

Default to `modern` unless the user specifies otherwise.

### Step 4: Generate Chart

**Tool**: `scripts/chart_create.py`

```bash
python3 scripts/chart_create.py data.csv \
  --type bar \
  --style modern \
  --title "Monthly Revenue 2024" \
  --xlabel "Month" --ylabel "Revenue ($)" \
  -o chart.png
```

**Common options:**
```bash
# Line chart with multiple series
python3 scripts/chart_create.py data.csv --type line --columns revenue,expenses -o trend.png

# Pie chart from a single column
python3 scripts/chart_create.py data.csv --type pie --label-col category --value-col count -o breakdown.png

# Scatter plot with trend line
python3 scripts/chart_create.py data.csv --type scatter --x price --y sales --trend -o correlation.png

# Heatmap from a matrix CSV
python3 scripts/chart_create.py matrix.csv --type heatmap --cmap viridis -o heatmap.png

# Export as SVG for web use
python3 scripts/chart_create.py data.csv --type bar -o chart.svg --format svg
```

### Step 5: Iterate

Show the generated chart to the user. Offer adjustments:

- Change colors: `--palette "#2563EB,#DC2626,#16A34A"`
- Adjust size: `--width 12 --height 6`
- Add annotations: `--annotate`
- Change chart type: `--type line`
- Export different format: `--format svg` or `--format pdf`

Regenerate until the user is satisfied.

### Step 6: Deliver

Output format:
1. Chart file path
2. Brief description of what the chart shows

```
Chart created: "Monthly Revenue 2024"
  File: chart.png (1200x800, 45KB)
  Type: bar chart
  Data: 12 months, revenue range $45K-$120K
```

## Rules

- Always label axes. Charts without labels are useless.
- Use readable font sizes. Title: 16pt, axis labels: 12pt, tick labels: 10pt.
- Limit pie charts to 6 slices max. Group small values as "Other".
- For time series, always sort by date on the x-axis.
- Default output size: 10x6 inches at 150 DPI (1500x900px). Adjust for specific needs.
- Prefer PNG for general use, SVG for web, PDF for print.
