---
name: minimax-pdf-read
description: >
  Extract and analyze text content from PDF documents. Use when: user shares a .pdf file
  path (any message containing .pdf file extension) or uses any of these words/phrases
  near a PDF: "read this PDF", "extract text from", "what does this PDF say", "analyze
  this PDF", " summarize this PDF", "get text from", "parse this PDF", "tell me what's
  in this PDF", "extract content from", "read the attached PDF".
  Triggers: any message with a .pdf file extension, or any request to read, extract,
  analyze, summarize, or parse a PDF document.
license: MIT
metadata:
  version: "1.0"
  category: document-processing
---

# minimax-pdf-read

Extract and analyze text content from PDF documents using Python.

## Prerequisites

- Python 3.9+
- Install dependencies: `pip install -r skills/minimax-pdf-read/scripts/requirements.txt`
- No external API keys required — uses local text extraction

## Quick Start

```bash
pip install -r skills/minimax-pdf-read/scripts/requirements.txt
python skills/minimax-pdf-read/scripts/extract.py --input document.pdf
```

## Scripts

| Script | Purpose | Usage |
|---|---|---|
| `extract.py` | Extract text and metadata from PDFs | See Usage below |
| `requirements.txt` | Python dependencies | `pip install -r requirements.txt` |

## Usage

### Extract all text from a PDF

```bash
python skills/minimax-pdf-read/scripts/extract.py --input document.pdf
```

### Extract text from specific pages

```bash
python skills/minimax-pdf-read/scripts/extract.py --input document.pdf --pages 1-5
```

### Extract to a file

```bash
python skills/minimax-pdf-read/scripts/extract.py --input document.pdf --output extracted.txt
```

### Get PDF metadata only

```bash
python skills/minimax-pdf-read/scripts/extract.py --input document.pdf --metadata
```

## Workflow

### Step 1: Detect PDF

The skill triggers when a message contains a `.pdf` file path or URL.

### Step 2: Extract text

Use the extraction script:

```bash
python skills/minimax-pdf-read/scripts/extract.py --input document.pdf
```

Or use pypdf directly for custom processing:

```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")
for page in reader.pages:
    text = page.extract_text()
    print(text)
```

### Step 3: Present results

Return the extracted text clearly, preserving structure where possible.

## Output Format

```
## Extracted Text

[Full text content from the PDF, page by page]

## Metadata

- Pages: N
- Title: [if available]
- Author: [if available]
```

## Notes

- pypdf works best on text-based PDFs
- Scanned/image PDFs may require OCR (see vision-analysis skill)
- Large PDFs may need page-by-page extraction
