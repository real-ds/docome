# Docome Development Guide

## 1. Development Philosophy

Docome is engine-first.

The Web UI, CLI and API must consume shared application services. Document
processing logic must never be duplicated across interfaces.

## 2. Architecture

Web → FastAPI → Application Services → Document Engines

CLI → Application Services → Document Engines

API → Application Services → Document Engines

## 3. Repository Layout

```text
docome/
├── apps/
│   ├── web/
│   └── api/
├── packages/
│   ├── pdf_engine/
│   ├── conversion_engine/
│   ├── image_engine/
│   ├── signature_engine/
│   ├── ocr_engine/
│   └── document_engine/
├── cli/
├── workers/
├── tests/
├── scripts/
├── infra/
└── docs/
```

## 4. Job Processing

Long-running work should use a job model:

`queued → processing → completed | failed | cancelled`

Every job should have a stable job ID.

## 5. File Lifecycle

Upload → Validate → Queue → Process → Validate Output → Store Result →
Return Result → Cleanup

## 6. Validation

Never trust:

- file extension
- MIME type supplied by client
- filenames
- archive contents

Validate file signatures and document structure.

## 7. Testing

Every feature needs:

- unit tests
- integration tests

Conversion/editor features additionally need visual regression tests.

## 8. Visual Regression

For layout-sensitive operations:

1. Process fixture
2. Render output pages to images
3. Compare against reference images
4. Record meaningful differences
5. Reject regressions

## 9. CLI Parity

When an operation is deterministic and useful for automation, expose it
through CLI using the same service used by the Web/API.

## 10. Security

Protect against:

- path traversal
- SSRF
- malicious PDFs
- decompression bombs
- oversized files
- command injection
- unsafe temporary files
- unauthorized document access

## 11. Code Quality

Use:

- Ruff
- Black
- Mypy
- Pytest

Keep modules small and domain-oriented.

## 12. Definition of Done

A feature is complete when implementation, tests, validation, errors,
documentation and security considerations are covered.
