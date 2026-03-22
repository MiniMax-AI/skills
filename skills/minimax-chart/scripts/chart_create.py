#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Chart generator — create publication-ready charts from CSV/JSON data.

Usage:
  python chart_create.py data.csv -o chart.png
  python chart_create.py data.csv --type line --columns revenue,expenses -o trend.png
  python chart_create.py data.csv --type pie --label-col category --value-col count -o pie.png
  python chart_create.py data.csv --type scatter --x price --y sales --trend -o scatter.png

Requires: matplotlib, pandas
"""

import argparse
import json
import os
import sys

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError:
    raise SystemExit("ERROR: matplotlib and pandas are required.\n  pip install matplotlib pandas")

# Style presets
STYLES = {
    "modern": {
        "colors": ["#2563EB", "#DC2626", "#16A34A", "#F59E0B", "#8B5CF6", "#06B6D4"],
        "bg": "#FFFFFF",
        "grid_color": "#E5E7EB",
        "text_color": "#1F2937",
        "font_family": "sans-serif",
    },
    "vibrant": {
        "colors": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8", "#F7DC6F"],
        "bg": "#FFFFFF",
        "grid_color": "#E0E0E0",
        "text_color": "#2D3436",
        "font_family": "sans-serif",
    },
    "academic": {
        "colors": ["#2C3E50", "#7F8C8D", "#BDC3C7", "#95A5A6", "#34495E", "#ABB2B9"],
        "bg": "#FFFFFF",
        "grid_color": "#D5D8DC",
        "text_color": "#2C3E50",
        "font_family": "serif",
    },
    "dark": {
        "colors": ["#00D2FF", "#FF6B6B", "#A8E6CF", "#FFD93D", "#C792EA", "#FF8A65"],
        "bg": "#1A1A2E",
        "grid_color": "#2D2D44",
        "text_color": "#E0E0E0",
        "font_family": "sans-serif",
    },
}


def _load_data(path: str) -> pd.DataFrame:
    """Load data from CSV or JSON file."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path)
    elif ext == ".tsv":
        return pd.read_csv(path, sep="\t")
    elif ext == ".json":
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif "labels" in data and "values" in data:
            return pd.DataFrame({"label": data["labels"], "value": data["values"]})
        else:
            return pd.DataFrame(data)
    else:
        return pd.read_csv(path)


def _apply_style(style_name: str):
    """Apply a style preset to matplotlib."""
    style = STYLES.get(style_name, STYLES["modern"])
    plt.rcParams.update({
        "figure.facecolor": style["bg"],
        "axes.facecolor": style["bg"],
        "axes.edgecolor": style["grid_color"],
        "axes.grid": True,
        "grid.color": style["grid_color"],
        "grid.alpha": 0.5,
        "text.color": style["text_color"],
        "axes.labelcolor": style["text_color"],
        "xtick.color": style["text_color"],
        "ytick.color": style["text_color"],
        "font.family": style["font_family"],
        "font.size": 10,
        "axes.titlesize": 16,
        "axes.labelsize": 12,
    })
    return style["colors"]


def _auto_detect_type(df: pd.DataFrame) -> str:
    """Auto-detect the best chart type based on data shape."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Try to detect datetime columns
    for col in cat_cols[:]:
        try:
            pd.to_datetime(df[col])
            cat_cols.remove(col)
        except (ValueError, TypeError):
            pass

    if len(numeric_cols) == 2 and len(cat_cols) == 0:
        return "scatter"
    elif len(numeric_cols) == 1 and len(cat_cols) == 1:
        if len(df) <= 6:
            return "pie"
        return "bar"
    elif len(numeric_cols) >= 2 and len(cat_cols) >= 1:
        return "line"
    elif len(numeric_cols) == 1 and len(cat_cols) == 0:
        return "histogram"
    else:
        return "bar"


def _chart_bar(df, args, colors):
    fig, ax = plt.subplots(figsize=(args.width, args.height))
    cols = args.columns.split(",") if args.columns else df.select_dtypes(include=["number"]).columns.tolist()[:3]
    x_col = args.label_col or df.columns[0]
    x = range(len(df))
    width = 0.8 / len(cols)
    for i, col in enumerate(cols):
        offset = (i - len(cols) / 2 + 0.5) * width
        ax.bar([xi + offset for xi in x], df[col], width=width, label=col, color=colors[i % len(colors)])
    ax.set_xticks(x)
    ax.set_xticklabels(df[x_col], rotation=45, ha="right")
    if len(cols) > 1:
        ax.legend()
    return fig, ax


def _chart_line(df, args, colors):
    fig, ax = plt.subplots(figsize=(args.width, args.height))
    cols = args.columns.split(",") if args.columns else df.select_dtypes(include=["number"]).columns.tolist()[:5]
    x_col = args.label_col or df.columns[0]
    for i, col in enumerate(cols):
        ax.plot(df[x_col], df[col], marker="o", markersize=4, label=col, color=colors[i % len(colors)], linewidth=2)
    ax.legend()
    plt.xticks(rotation=45, ha="right")
    return fig, ax


def _chart_scatter(df, args, colors):
    fig, ax = plt.subplots(figsize=(args.width, args.height))
    x_col = args.x or df.select_dtypes(include=["number"]).columns[0]
    y_col = args.y or df.select_dtypes(include=["number"]).columns[1]
    ax.scatter(df[x_col], df[y_col], color=colors[0], alpha=0.7, s=50)
    if args.trend:
        import numpy as np
        z = np.polyfit(df[x_col].astype(float), df[y_col].astype(float), 1)
        p = np.poly1d(z)
        ax.plot(sorted(df[x_col]), p(sorted(df[x_col])), "--", color=colors[1], linewidth=1.5, alpha=0.7)
    return fig, ax


def _chart_pie(df, args, colors):
    fig, ax = plt.subplots(figsize=(args.width, args.height))
    label_col = args.label_col or df.columns[0]
    value_col = args.value_col or df.select_dtypes(include=["number"]).columns[0]
    wedges, texts, autotexts = ax.pie(
        df[value_col], labels=df[label_col], colors=colors[:len(df)],
        autopct="%1.1f%%", startangle=90,
    )
    for t in autotexts:
        t.set_fontsize(9)
    ax.axis("equal")
    return fig, ax


def _chart_histogram(df, args, colors):
    fig, ax = plt.subplots(figsize=(args.width, args.height))
    col = args.columns.split(",")[0] if args.columns else df.select_dtypes(include=["number"]).columns[0]
    ax.hist(df[col], bins=args.bins, color=colors[0], edgecolor="white", alpha=0.8)
    return fig, ax


def _chart_heatmap(df, args, colors):
    fig, ax = plt.subplots(figsize=(args.width, args.height))
    numeric = df.select_dtypes(include=["number"])
    cmap = args.cmap or "YlOrRd"
    im = ax.imshow(numeric.values, cmap=cmap, aspect="auto")
    ax.set_xticks(range(len(numeric.columns)))
    ax.set_xticklabels(numeric.columns, rotation=45, ha="right")
    if df.columns[0] not in numeric.columns:
        ax.set_yticks(range(len(df)))
        ax.set_yticklabels(df.iloc[:, 0])
    fig.colorbar(im, ax=ax)
    return fig, ax


CHART_TYPES = {
    "bar": _chart_bar,
    "line": _chart_line,
    "scatter": _chart_scatter,
    "pie": _chart_pie,
    "histogram": _chart_histogram,
    "heatmap": _chart_heatmap,
}


def main():
    p = argparse.ArgumentParser(description="Chart generator from CSV/JSON data")
    p.add_argument("data", help="Input data file (CSV, TSV, or JSON)")
    p.add_argument("-o", "--output", required=True, help="Output file path (png/svg/pdf)")
    p.add_argument("--type", default="auto", choices=list(CHART_TYPES.keys()) + ["auto"], help="Chart type (default: auto-detect)")
    p.add_argument("--style", default="modern", choices=list(STYLES.keys()), help="Visual style preset (default: modern)")
    p.add_argument("--title", default="", help="Chart title")
    p.add_argument("--xlabel", default="", help="X-axis label")
    p.add_argument("--ylabel", default="", help="Y-axis label")
    p.add_argument("--columns", default="", help="Comma-separated column names to plot")
    p.add_argument("--label-col", default="", help="Column to use for labels/categories")
    p.add_argument("--value-col", default="", help="Column to use for values (pie charts)")
    p.add_argument("--x", default="", help="X-axis column (scatter)")
    p.add_argument("--y", default="", help="Y-axis column (scatter)")
    p.add_argument("--trend", action="store_true", help="Add trend line (scatter)")
    p.add_argument("--palette", default="", help="Custom colors (comma-separated hex codes)")
    p.add_argument("--width", type=float, default=10, help="Figure width in inches (default: 10)")
    p.add_argument("--height", type=float, default=6, help="Figure height in inches (default: 6)")
    p.add_argument("--dpi", type=int, default=150, help="Output DPI (default: 150)")
    p.add_argument("--format", default="", help="Output format override (png/svg/pdf)")
    p.add_argument("--bins", type=int, default=20, help="Number of bins for histogram (default: 20)")
    p.add_argument("--cmap", default="", help="Colormap for heatmap (default: YlOrRd)")
    p.add_argument("--annotate", action="store_true", help="Add value annotations on bars")
    args = p.parse_args()

    if not os.path.exists(args.data):
        raise SystemExit(f"ERROR: Data file not found: {args.data}")

    df = _load_data(args.data)
    print(f"Data loaded: {len(df.columns)} columns, {len(df)} rows")
    for col in df.columns:
        dtype = "numeric" if pd.api.types.is_numeric_dtype(df[col]) else "text"
        print(f"  {col} ({dtype}): {df[col].nunique()} unique values")

    chart_type = args.type
    if chart_type == "auto":
        chart_type = _auto_detect_type(df)
        print(f"Auto-detected chart type: {chart_type}")

    colors = _apply_style(args.style)
    if args.palette:
        colors = args.palette.split(",")

    chart_fn = CHART_TYPES[chart_type]
    fig, ax = chart_fn(df, args, colors)

    if args.title:
        ax.set_title(args.title, pad=15, fontweight="bold")
    if args.xlabel:
        ax.set_xlabel(args.xlabel)
    if args.ylabel:
        ax.set_ylabel(args.ylabel)

    if args.annotate and chart_type == "bar":
        for container in ax.containers:
            ax.bar_label(container, fmt="%.0f", fontsize=8, padding=2)

    plt.tight_layout()

    fmt = args.format or os.path.splitext(args.output)[1].lstrip(".")
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    fig.savefig(args.output, dpi=args.dpi, format=fmt or "png", bbox_inches="tight")
    plt.close(fig)

    size = os.path.getsize(args.output)
    print(f"\nOK: {size:,} bytes -> {args.output}")
    print(f"  Type: {chart_type}")
    print(f"  Style: {args.style}")
    print(f"  Size: {int(args.width * args.dpi)}x{int(args.height * args.dpi)}px @ {args.dpi} DPI")


if __name__ == "__main__":
    main()
