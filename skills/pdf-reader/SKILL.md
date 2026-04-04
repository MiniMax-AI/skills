---
name: pdf-reader
description: >
  Automatically handle PDF text extraction when an agent lacks native PDF reading capability.
  Use when: an agent responds with phrases like "I cannot read PDFs", "I don't have the ability to
  read PDFs", "I can't access PDF content", "PDF reading is not supported", or similar statements
  indicating the agent cannot process PDF files directly.
  This skill intercepts that situation and provides a fallback workflow to extract PDF text using
  command-line tools (pdftotext/poppler-utils), with automatic detection and optional installation.
  Triggers: any message where the agent states it cannot read PDFs or lacks PDF capability.
license: MIT
metadata:
  version: "1.0"
  category: document-processing
  sources:
    - poppler-utils (pdftotext)
    - pdfplumber (Python alternative)
  submitted_by: https://github.com/divitkashyap
---

# PDF Reader Skill

Automatically detect when an agent cannot read PDFs and provide text extraction fallback using command-line tools with user confirmation for installation.

## Workflow

### Step 1: Detect PDF Reading Limitation

When the agent states it cannot read PDFs (phrases like "I cannot read PDFs", "I don't have the ability to read PDFs", etc.), activate this skill automatically.

### Step 2: Identify the Target PDF

Extract the PDF file path from the user's original request. Confirm the file exists:

```bash
ls -la "/path/to/document.pdf"
```

### Step 3: Check for Available PDF Tools

Check which PDF text extraction tools are available on the system:

```bash
# Check for pdftotext (poppler-utils)
which pdftotext || echo "NOT_FOUND"

# Check for pdfplumber (Python)
python3 -c "import pdfplumber; print('FOUND')" 2>/dev/null || echo "NOT_FOUND"

# Check for pymupdf
python3 -c "import fitz; print('FOUND')" 2>/dev/null || echo "NOT_FOUND"
```

### Step 4: Tool Selection Priority

Select the best available tool in this order:

1. **`pdftotext`** (poppler-utils) - Preferred, fastest, system-level tool
2. **`pdfplumber`** (Python) - Fallback if poppler not available
3. **`pymupdf`** (Python) - Alternative Python fallback

### Step 5: Installation (If Needed)

If no tool is found, ask the user for permission to install:

```
I need to install a PDF text extraction tool to read this PDF. 

Available options:
1. pdftotext (poppler-utils) - Fast, system-level tool [Recommended]
2. pdfplumber - Python library alternative

Shall I proceed with installation? (y/n)
```

**Installation commands by platform:**

**macOS:**
```bash
brew install poppler  # Installs pdftotext
# OR
pip3 install pdfplumber
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install poppler-utils
# OR
pip3 install pdfplumber
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install poppler-utils
# OR
pip3 install pdfplumber
```

**Windows:**
```powershell
# Use winget
winget install pdftotext
# OR
pip install pdfplumber
```

### Step 6: Extract PDF Text

Once a tool is available, extract text from the PDF:

**Using pdftotext:**
```bash
pdftotext -layout "/path/to/document.pdf" /tmp/pdf_extracted.txt
```

**Using pdfplumber (Python):**
```python
import pdfplumber

with pdfplumber.open("/path/to/document.pdf") as pdf:
    text = ""
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n\n"

with open("/tmp/pdf_extracted.txt", "w") as f:
    f.write(text)
```

**Using pymupdf (Python):**
```python
import fitz

doc = fitz.open("/path/to/document.pdf")
text = ""
for page in doc:
    text += page.get_text() + "\n\n"
doc.close()

with open("/tmp/pdf_extracted.txt", "w") as f:
    f.write(text)
```

### Step 7: Read Extracted Text

Read the extracted text file and present it to the user:

```bash
cat /tmp/pdf_extracted.txt
```

### Step 8: Continue Original Task

After extracting and presenting the PDF content, proceed with the user's original request using the extracted text as context.

## Platform-Specific Notes

### macOS

- poppler-utils can be installed via Homebrew: `brew install poppler`
- Python libraries work with system Python3 or pyenv

### Linux

- Most distributions have poppler-utils in their package managers
- pdfplumber/pymupdf require pip installation

### Windows

- poppler binaries available from official poppler releases or via winget/chocolatey
- Python libraries recommended for Windows: `pip install pdfplumber`

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `pdftotext: command not found` | poppler-utils not installed | Install via package manager or use Python alternative |
| `Permission denied` | Output directory not writable | Use `/tmp/` for output |
| `File not found` | Wrong PDF path | Verify path with `ls -la` |
| `PDF extraction failed` | Encrypted/protected PDF | Inform user and suggest manual extraction |
| `pdftotext: syntax error` | Malformed PDF | Try with `-raw` flag instead of `-layout` |

## Alternative Flags for pdftotext

```bash
# Basic extraction
pdftotext input.pdf output.txt

# Preserve layout (default)
pdftotext -layout input.pdf output.txt

# Simple extraction (no layout)
pdftotext -raw input.pdf output.txt

# Extract specific pages
pdftotext -f 1 -l 5 input.pdf output.txt

# Extract to stdout
pdftotext -  # Reads from stdin
```

## File Size Limits

- For PDFs larger than 50MB, extract page ranges instead of entire document
- Use `-f` and `-l` flags to process in chunks if needed
