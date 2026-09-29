# Changelog

All notable changes to Docome will be documented in this file.

## [Unreleased]

### Added
- Element inspection: `list_elements`, `find_element`, `find_elements_in_rect`, and `get_element` on `EditorSession`, with stable element IDs per page
- `packages/pdf_engine/elements.py` enumerates text spans, images, vector drawings, and annotations with bounding boxes, font details, and annotation content
- CLI: `docome edit elements` (with `--page`, `--kind`, `--json`) and `docome edit pick --x --y` for hit testing
- REST API: `POST /api/v1/edit/elements` and `POST /api/v1/edit/elements/pick`
- `EditorSession` now supports `with` so the PDF file handle is always released
- REST API: `POST /api/v1/edit/apply` and `GET /api/v1/edit/actions` exposing the same edit-plan engine as the CLI
- REST API: `POST /api/v1/convert/pdf2docx-hq` and `POST /api/v1/convert/fidelity`
- `apps/api/app/core/workspace.py` for cross-platform, self-cleaning temp workspaces and filename sanitization
- Pydantic request models for edit plans with per-field validation and size limits
- Multi-step edit plans: apply a JSON list of operations in one session (`packages/pdf_engine/edit_plan.py`)
- CLI: `docome edit apply --plan`, `docome edit undo --times`, and `docome edit actions`
- Plan validation with the failing operation index reported, and non-zero exit on failure
- `undo_depth`, `redo_depth`, and `page_count` on `EditorSession`
- Automated conversion fidelity harness (`packages/conversion_engine/fidelity.py`) scoring page count, text, fonts, tables, images, and hyperlinks
- CLI: `docome convert fidelity input.pdf -o output.docx` with table and `--json` output, exiting non-zero on threshold failure
- Per-cell font capture so table text keeps its family, size, weight, and color
- High-fidelity PDF to DOCX reconstruction (`docome convert pdf2docx-hq`)
- Paragraph reconstruction by merging wrapped lines with matching fonts
- Font mapping to real families (Arial, Times New Roman, Courier New, Symbol, Wingdings) with size, bold, italic, and color
- Table detection and reconstruction via vector grid analysis
- Image extraction with aspect-preserving placement
- Working external hyperlinks (`w:hyperlink` with relationships)
- Bullet and numbered list detection with indent-based nesting levels
- Multi-column detection with true DOCX column layout and reading order
- Header and footer extraction into real DOCX headers and footers
- PDF page size and margin mapping to DOCX sections
- Alignment inference (left, right, center) from page geometry

### Fixed
- `move_element` and `resize_element` filled the source rectangle with opaque white before pasting a rasterized copy, which destroyed any text, image, or table underneath and left a visible white block. They now redact the region without painting a fill, so surrounding content is preserved
- `move_element` and `resize_element` accepted empty or non-positive rectangles, producing corrupt or empty output. Invalid geometry is now rejected
- `docx_to_pdf` was a stub that created one blank A4 page per paragraph and drew plain text at a fixed offset. It now renders the real document through the MuPDF Story layout engine, preserving page size, margins, headings, fonts, sizes, bold, italic, underline, color, alignment, list markers, indents, tables with borders and shading, and embedded images, with genuine reflow and pagination. Content that cannot fit the page frame now raises a clear error instead of looping forever
- `docx_to_pdf` read only `Document.paragraphs`, so tables and images were silently dropped. The document body is now walked in order, so mixed content keeps its sequence
- The PDF operation routes (merge, split, extract, rotate, compress, metadata, page count) no longer hardcode `/tmp` paths, so they work on Windows. They now live in `apps/api/app/api/routes/pdf_ops.py`, use the same workspace helper as the new routes, return in-memory bytes, and are covered by tests
- `POST /api/v1/pdf/split` returns a real ZIP when the input produces more than one part, instead of pointing at files that were already deleted
- `POST /api/v1/pdf/extract` rejected valid input unless a page list was passed, because it tested a loop variable with `in dir()`; it now accepts either a page list or a `start`/`end` range and reports which one is missing
- `POST /api/v1/pdf/merge` raised `NameError` on engine failure because `output_path` was never assigned before the `finally` cleanup block
- API file responses are now returned as in-memory bytes, so downloads no longer depend on temp files that are deleted before the body is streamed
- Uploads are written to a separate input directory, so an upload named `input.pdf` no longer collides with its own output path and fail with "save to original must be incremental"
- Uploaded filenames are sanitized, so `../../etc/passwd.pdf` cannot escape the workspace
- `delete_text` painted a white overlay instead of removing text; it now uses redactions so deleted content no longer extracts, copies, or searches
- `replace_text` left the original text in the content stream for the same reason
- Bold and italic span flags were swapped (bold is flag 16, italic is flag 2)
- Hyperlink writer used a nonexistent `Run.hyperlink` API and silently produced plain text
- Stale column indices leaked between detection passes

### Known Issues
- DOCX to PDF rendering uses the MuPDF Story engine with Base-14 and bundled fallback fonts. Exact font matching to installed Windows fonts (Calibri, Arial) is not yet reproduced, and DOCX headers, footers, and footnotes are not rendered.
- Pixel-level round-trip verification is still unavailable because LibreOffice or Word is not installed in the test environment.

## [0.1.0] - 2024

### Added
- PDF Operations: merge, split, extract, remove, rotate, compress
- PDF metadata read/write
- PDF password protection
- Image to PDF conversion
- PDF to image conversion
- Document conversion: DOCX, XLSX, PPTX, TXT, Markdown
- OCR support (Tesseract, EasyOCR)
- E-signature creation and placement
- Form fields: text, date, checkbox
- Windows CLI executable
- Windows GUI application
- REST API endpoints
