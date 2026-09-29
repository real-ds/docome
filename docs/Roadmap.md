# Docome Roadmap

## Phase 0 — Foundation

- repository
- architecture
- CI
- Docker
- FastAPI skeleton
- CLI skeleton
- storage abstraction
- job abstraction

## Phase 1 — PDF Core

- merge
- split
- extract
- remove
- reorder
- rotate
- compress
- metadata
- protect
- images → PDF
- PDF → images

## Phase 2 — Conversion

- DOCX → PDF
- PDF → DOCX
- XLSX → PDF
- PDF → XLSX
- PPTX → PDF
- PDF → PPTX
- HTML → PDF
- PDF → Markdown
- PDF → TXT

## Phase 3 — Real Editor

- PDF.js viewer
- page thumbnails
- element selection
- text editing
- image editing
- shapes
- annotations
- undo/redo
- save/export

### Status

Engine, CLI, and REST API are complete for: page thumbnails, element
selection and hit testing, text editing and true deletion, image editing,
shapes, annotations, undo/redo, and save/export. Each is exposed by all
three surfaces through the shared packages, never by duplicated logic.

Still open:

- PDF.js viewer in the web app. It should consume the element and
  thumbnail endpoints already available rather than reimplementing
  document processing.
- DOCX → PDF does not yet reproduce installed Windows fonts exactly and
  does not render DOCX headers, footers, or footnotes.
- `move` and `resize` relocate a region by redaction plus a rasterized
  copy, so moved text is no longer selectable or searchable afterwards.
  Moving text as real text is the natural follow-up.
- Pixel-level round-trip verification is blocked on LibreOffice or Word
  being installed in the test environment.

## Phase 4 — Paid/Professional

- e-signature
- signature requests
- image background removal
- forms
- redaction
- compare
- Bates numbering
- PDF/A
- accessibility
- preflight

## Phase 5 — Intelligent Documents

- OCR
- AI extraction
- summarization
- document Q&A
- table extraction
- translation
- smart redaction
- multi-document analysis

## Phase 6 — SaaS

- accounts
- history
- storage
- subscriptions
- usage limits
- teams
- API keys
- audit logs
- enterprise controls
