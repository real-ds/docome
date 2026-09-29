# Docome — Claude/Coding Agent Instructions

## Mission

Build a production-grade all-in-one PDF/document platform around a shared
Python document engine.

## Non-Negotiable Principles

### 1. Do not fake PDF editing

If a feature claims to edit existing PDF content, it must operate on the
underlying content where technically possible. Overlay hacks are not an
acceptable substitute for real editing.

### 2. Preserve layout

For PDF → DOCX, prioritize:

- fonts
- text positions
- paragraphs
- tables
- images
- headers
- footers
- columns
- page breaks

Do not label a converter high-fidelity without benchmark evidence.

### 3. One processing engine

Web, API and CLI must use shared application services.

### 4. Python-first backend

Document processing belongs in Python. The frontend is an interface, not
the document engine.

### 5. Heavy jobs are asynchronous

OCR, large conversion, batch processing and complex document analysis
must not block HTTP requests.

### 6. Uploaded documents are untrusted

Validate every file and protect the filesystem and processing environment.

### 7. Never leak internal errors

Do not expose stack traces, local paths, secrets or implementation details
to users.

### 8. Tests are mandatory

Every new feature needs tests. Layout-sensitive features need visual tests.

### 9. Avoid unnecessary dependencies

Before adding a library, assess whether existing dependencies solve the
problem, then check maintenance, security and licensing.

### 10. Avoid premature microservices

Use a modular monolith initially.

### 11. Do not silently lower quality

If a conversion cannot preserve a feature, report the limitation rather
than silently producing a misleading result.

### 12. Keep CLI automation-friendly

Provide stable exit codes and `--json` output for scripting.

## Completion Checklist

Before declaring a feature done:

- implementation complete
- tests passing
- validation present
- errors structured
- security reviewed
- docs updated
- CLI/API support considered
- output manually or visually verified where appropriate
