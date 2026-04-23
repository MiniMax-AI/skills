#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("ERROR: pypdf is not installed. Run: pip install pypdf")


def extract_text(pdf_path: Path, pages: str = None) -> str:
    reader = PdfReader(pdf_path)

    if pages:
        page_range = parse_page_range(pages, len(reader.pages))
        pages_to_extract = [reader.pages[i] for i in page_range]
    else:
        pages_to_extract = reader.pages

    output = []
    for i, page in enumerate(pages_to_extract, 1):
        text = page.extract_text()
        output.append(f"--- Page {i} ---\n{text}")

    return "\n\n".join(output)


def extract_metadata(pdf_path: Path) -> dict:
    reader = PdfReader(pdf_path)
    info = reader.metadata or {}

    return {
        "pages": len(reader.pages),
        "title": info.get("/Title", "N/A"),
        "author": info.get("/Author", "N/A"),
        "subject": info.get("/Subject", "N/A"),
        "creator": info.get("/Creator", "N/A"),
    }


def parse_page_range(pages_str: str, total_pages: int) -> list:
    result = []
    parts = pages_str.split(",")
    for part in parts:
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start_idx = max(0, int(start.strip()) - 1)
            end_idx = min(total_pages, int(end.strip()))
            result.extend(range(start_idx, end_idx))
        else:
            result.append(max(0, min(total_pages - 1, int(part) - 1)))
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Extract text and metadata from PDF documents."
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Input PDF file path"
    )
    parser.add_argument(
        "--output", "-o", help="Output text file path (default: stdout)"
    )
    parser.add_argument(
        "--pages", "-p", help="Page range, e.g., '1-5' or '1,3,5-7'"
    )
    parser.add_argument(
        "--metadata", "-m", action="store_true", help="Extract metadata only"
    )

    args = parser.parse_args()

    pdf_path = Path(args.input)
    if not pdf_path.exists():
        sys.exit(f"ERROR: File not found: {pdf_path}")

    if not pdf_path.suffix.lower() == ".pdf":
        sys.exit("ERROR: Input file must be a PDF")

    try:
        if args.metadata:
            meta = extract_metadata(pdf_path)
            output = "\n".join(f"{k}: {v}" for k, v in meta.items())
        else:
            output = extract_text(pdf_path, args.pages)
    except Exception as e:
        sys.exit(f"ERROR: Failed to extract from PDF: {e}")

    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
