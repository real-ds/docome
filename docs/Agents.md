# Docome Agent Responsibilities

## Project Architect

Owns system architecture, boundaries and architectural decisions.

## PDF Engine Agent

Owns page operations, PDF parsing, structure, metadata, compression and
protection.

## Conversion Agent

Owns PDF ↔ Office conversion, HTML conversion and high-fidelity document
reconstruction.

## PDF Editor Agent

Owns real PDF editing, coordinate systems, text/image manipulation and
editor behavior.

## Image Agent

Owns image processing, background removal, transformations and PDF image
placement.

## OCR Agent

Owns OCR providers, searchable PDFs and OCR quality.

## Signature Agent

Owns signatures, signer workflows and audit trails.

## Web Agent

Owns the Next.js application and editor UI. It must not duplicate document
processing logic.

## CLI Agent

Owns Typer commands, terminal UX, JSON output and automation workflows.

## API Agent

Owns REST routes, authentication, validation and job endpoints.

## QA Agent

Owns unit, integration, conversion benchmark and visual regression testing.

## Security Agent

Owns uploaded-file security, access control, storage security and abuse
prevention.

## Documentation Agent

Owns technical documentation and usage documentation.

## Coordination Rule

Agents must respect domain ownership. Cross-domain changes should be
explicit and documented.
