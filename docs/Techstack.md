# Docome Tech Stack

## Backend

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

## PDF

- PyMuPDF
- pikepdf
- qpdf

Use adapters so individual libraries can be replaced.

## Office

- LibreOffice headless
- python-docx
- openpyxl
- python-pptx

## Images

- Pillow
- Pluggable background-removal provider

## OCR

Provider abstraction supporting local and external OCR engines.

Possible implementations:

- Tesseract
- PaddleOCR

## Web

- Next.js
- React
- TypeScript
- Tailwind CSS
- PDF.js

Potential editor canvas:

- Konva
- Fabric.js

## CLI

- Typer
- Rich

## Queue

- Redis
- Celery or RQ

## Database

- PostgreSQL

## Storage

- S3-compatible object storage
- MinIO for local development

## Testing

- Pytest
- pytest-asyncio
- HTTPX
- visual regression tooling

## Infrastructure

- Docker
- Docker Compose
- GitHub Actions

## Architecture Principle

Begin with a modular monolith. Introduce separate services only when a
measurable scaling, security or operational reason exists.
