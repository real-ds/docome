# Conversion Benchmarks

High-fidelity conversion is a flagship capability and requires measurable
testing.

## Fixture Categories

Maintain representative PDFs containing:

- simple paragraphs
- multiple fonts
- headings
- lists
- tables
- multi-column layouts
- images
- headers/footers
- page numbers
- hyperlinks
- forms
- scanned pages
- mixed content

## Metrics

Measure:

- text extraction accuracy
- font preservation
- positional accuracy
- table reconstruction
- image preservation
- page count preservation
- page-break preservation
- visual similarity

## Automated Fidelity Harness

Structural metrics are measured automatically by
`packages/conversion_engine/fidelity.py` and exercised in
`tests/unit/test_fidelity.py`. Score a conversion from the CLI:

```bash
docome convert pdf2docx-hq fixture.pdf -o fixture.docx
docome convert fidelity fixture.pdf -o fixture.docx
docome convert fidelity fixture.pdf -o fixture.docx --json
```

The report covers page count, text retention, font retention, tables,
images, and hyperlinks, and exits non-zero when a threshold is missed so it
can gate CI.

## Visual Test

```text
Fixture PDF
   ↓
PDF → DOCX
   ↓
DOCX → PDF
   ↓
Render pages
   ↓
Compare with reference
```

Pixel-level comparison requires a DOCX renderer, which is not installed in
the current environment (no LibreOffice/Word). Until one is available, the
fidelity harness covers the structural metrics above and pixel similarity
must be checked manually. Install LibreOffice and set it on `PATH` before
adding the render-and-diff stage.

Keep benchmark fixtures versioned and reproducible.
