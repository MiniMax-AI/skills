#!/usr/bin/env python3
"""
Add LaTeX formulas to DOCX file using minimax-docx CLI.

Usage:
    python3 add_latex_formulas.py <docx_file> <search_marker> [output_file]
    
Example:
    python3 add_latex_formulas.py document.docx "--- Formula Test ---"
"""

import subprocess
import sys
import os

MINIMAX_DOCX_CLI = "/tmp/skills-repo/skills/minimax-docx/scripts/dotnet/MiniMaxAIDocx.Cli"

# Formula templates
LATEX_FORMULAS = {
    "fraction": "$\\frac{x}{y}$",
    "sqrt": "$\\sqrt{x+y}$",
    "power": "$x^{2}$",
    "subscript": "$x_{i}$",
    "integral": "$\\int_{a}^{b} f(x) dx$",
    "sum": "$\\sum_{i=1}^{n} i^2$",
    "limit": "$\\lim_{x \\to \\infty} \\frac{1}{x}$",
    "derivative": "$\\frac{dy}{dx}$",
    "partial": "$\\frac{\\partial f}{\\partial x}$",
    "matrix": "$\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$",
    "euler": "$e^{i\\pi} + 1 = 0$",
    "emc2": "$E = mc^2$",
    "uncertainty": "$\\Delta x \\cdot \\Delta p \\geq \\frac{\\hbar}{2}$",
    "schrodinger": "$i\\hbar\\frac{\\partial}{\\partial t}\\Psi = \\hat{H}\\Psi$",
}

def add_formulas(docx_path, marker, output_path=None):
    """Add formulas to DOCX file."""
    if output_path is None:
        output_path = docx_path
    
    # Build formula text
    formulas_text = "\n".join([f"{i+1}. {f}" for i, f in enumerate(LATEX_FORMULAS.values())])
    replace_text = f"---\n{formulas_text}\n---"
    
    # Call minimax-docx CLI
    cmd = [
        "dotnet", "run", "--project", "MiniMaxAIDocx.Cli", "--",
        "edit", "replace-text",
        "--input", docx_path,
        "--output", output_path,
        "--search", marker,
        "--replace", replace_text
    ]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(MINIMAX_DOCX_CLI), capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"Success! Added {len(LATEX_FORMULAS)} formulas to {output_path}")
    else:
        print(f"Error: {result.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    docx_file = sys.argv[1]
    marker = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else None
    
    add_formulas(docx_file, marker, output)
