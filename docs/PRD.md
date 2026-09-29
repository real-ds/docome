# Docome — Product Requirements Document

## 1. Product Vision

Docome is an all-in-one PDF and document workspace combining free
document utilities with professional capabilities normally found in paid
PDF software.

The product provides Web, CLI and API interfaces over a shared Python
document-processing platform.

## 2. Product Positioning

The basic PDF utilities are table stakes. The primary differentiation is:

1. Real PDF editing
2. High-fidelity PDF → Word conversion
3. Professional document signing
4. Image upload and manipulation inside PDFs
5. Background removal and image composition
6. Professional document workflows
7. Future AI document intelligence

## 3. Core Modules

### A. PDF Organization

- Merge PDF
- Split PDF
- Extract pages
- Remove pages
- Reorder pages
- Organize PDF
- Rotate pages
- Insert pages
- Duplicate pages
- Extract all pages
- Split by page range
- Split every N pages
- Merge after split

### B. Optimize PDF

Compression levels:

- Extreme
- High
- Recommended
- Low/high-quality
- Custom

Optimization may include image downsampling, stream optimization,
metadata cleanup, duplicate-resource handling and object optimization.

### C. Conversion

#### To PDF

- DOC
- DOCX
- XLS
- XLSX
- PPT
- PPTX
- JPG/JPEG
- PNG
- TIFF
- HTML
- Web pages
- Images

#### From PDF

- DOCX
- XLSX
- PPTX
- JPG
- PNG
- TXT
- Markdown
- PDF/A

### D. Real PDF Editing

Users can edit existing PDF content where technically possible.

Capabilities:

- Edit existing text
- Delete existing text
- Replace existing text
- Move elements
- Resize elements
- Edit images
- Replace images
- Add text
- Add images
- Add shapes
- Add annotations
- Add links
- Typography controls

Important requirement: do not simulate existing-text editing merely by
placing a white rectangle over old text and drawing new text on top.

### E. High-Fidelity PDF → Word

This is a flagship feature.

Preserve:

- Font family
- Font size
- Font weight
- Text position
- Paragraph structure
- Tables
- Images
- Headers
- Footers
- Columns
- Lists
- Hyperlinks
- Page breaks

The implementation should use a document reconstruction pipeline rather than
simple text extraction.

### F. Image Workspace

Users can:

- Upload a picture
- Remove background
- Crop
- Resize
- Rotate
- Flip
- Change opacity
- Place anywhere on a PDF
- Move and resize after placement

### G. E-Signature

Support:

- Draw signature
- Type signature
- Upload signature
- Initials
- Date
- Text fields
- Checkboxes
- Multiple signers
- Sequential signing
- Signature requests
- Tracking
- Audit trail

### H. OCR

Create searchable/selectable PDFs from scanned documents.

### I. Forms

- Text fields
- Checkboxes
- Radio buttons
- Dropdowns
- Date fields
- Signature fields

### J. Security

- Password protection
- Encryption
- Permission controls
- Authorized PDF unlocking
- Metadata removal
- Permanent redaction

### K. Professional Tools

- Watermarks
- Page numbering
- Crop
- PDF comparison
- PDF/A
- Bates numbering
- Accessibility checks
- Print preflight

### L. Future AI

- Summarization
- Document Q&A
- Table extraction
- Structured data extraction
- Smart redaction
- Translation
- Multi-document analysis

## 4. Interfaces

### Web

Modern document workspace with upload, preview, page thumbnails, editor,
conversion flows, signing and history.

### CLI

All deterministic document operations should be scriptable.

### API

REST API under `/api/v1/`.

## 5. Non-Functional Requirements

- Secure handling of untrusted files
- Async processing for large jobs
- Deterministic core operations
- Visual regression testing for layout-sensitive conversion
- Structured errors
- Observability
- Reproducible processing
- Configurable temporary-file retention

## 6. Success Criteria

The first release should demonstrate:

- reliable core PDF manipulation
- high-quality compression
- working document conversion
- a credible PDF editor
- CLI/Web feature parity for core operations
- extensible processing architecture
