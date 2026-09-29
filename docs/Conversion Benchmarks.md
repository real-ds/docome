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

Keep benchmark fixtures versioned and reproducible.
