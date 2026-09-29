# Docome CLI

## Installation

During development:

```bash
pip install -e ".[dev]"
```

## Examples

```bash
docome pdf merge a.pdf b.pdf -o merged.pdf

docome pdf split document.pdf -p 1-5 -o output/

docome pdf compress document.pdf -l recommended -o compressed.pdf

docome convert pdf2docx document.pdf -o document.docx

docome pdf pdf2img document.pdf -o images/

docome ocr pdf2searchable scanned.pdf -o searchable.pdf

docome pdf rotate document.pdf -d 90 -o rotated.pdf
```

## Automation

Machine-readable output via `--json` flag.

Machine-readable output should contain:

- success
- operation
- input
- output
- duration
- warnings
- errors
