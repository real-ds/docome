# Docome Architecture

## Core Principle

The Python document-processing engine is the center of the product.

```text
Web
 │
 ▼
FastAPI
 │
 ▼
Application Services
 │
 ▼
Python Document Engine
 │
 ├── PDF Engine
 ├── Conversion Engine
 ├── Image Engine
 ├── OCR Engine
 └── Signature Engine

CLI ───────────────┘
```

## Layers

### Interface Layer

- Next.js Web
- CLI
- REST API

### Application Layer

Coordinates workflows and jobs.

### Domain Layer

Contains document concepts and business rules.

### Engine Layer

Contains low-level processing adapters.

### Infrastructure Layer

Contains:

- PostgreSQL
- Redis
- Object storage
- Worker runtime

## Job Architecture

```text
Request
  ↓
Job creation
  ↓
Queue
  ↓
Worker
  ↓
Processing Engine
  ↓
Output validation
  ↓
Object storage
  ↓
Download URL
```

## Storage

Do not store large PDF binaries directly in PostgreSQL.

Use object storage and store document metadata/database references in
PostgreSQL.

## Scaling

Start as a modular monolith.

Workers can scale horizontally before splitting the API or processing
engine into separate deployable services.
