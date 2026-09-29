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

## Development Loop — The Stable Progress Protocol

This loop governs how every agent writes, validates, and ships code. The goal is **stable, tested increments** — not raw velocity.

### 1. Plan the Increment
- Pick ONE deliverable from the current sprint backlog
- Define the acceptance criteria (what "done" looks like)
- Identify affected modules and tests needed
- Write a failing test first (TDD) or define the test cases

### 2. Write Minimal Implementation
- Implement only what satisfies the acceptance criteria
- No speculative features, no premature abstraction
- Keep changes focused to the owning agent's domain
- Follow existing patterns in the codebase

### 3. Test Relentlessly
- **Unit tests**: Every new function/class must have tests
- **Integration tests**: Cross-module behavior
- **Regression**: Run full suite (`pytest tests/`) — must pass 100%
- **Manual verification**: Exercise the CLI/API with real files

### 4. Validate Stability
- No test flakes — re-run if intermittent
- No new lint/type errors (`ruff`, `mypy` if configured)
- No broken imports or circular dependencies
- Performance: no O(n²) regressions on typical workloads

### 5. Commit — Only When Green
```
git add -A
git commit -m "<agent>: <deliverable> - <what changed>

- <specific change 1>
- <specific change 2>
- Tests: <count> passing"
```
- Commit message must reference the sprint/deliverable
- Each commit = one logical, testable increment
- No WIP commits, no "fix tests" commits after the fact

### 6. Push & Document
- Push to origin
- Update CHANGELOG.md with the change
- Update relevant docs (README, CLI.md, Architecture.md)
- Close/move the task in the sprint board

### Anti-Patterns (Do Not Do)
- ❌ Commit failing tests "to fix later"
- ❌ Bundle multiple deliverables in one commit
- ❌ Skip tests because "it's simple"
- ❌ Push directly to main without PR/review
- ❌ Add features not in the sprint backlog

### Definition of Done (Per Increment)
- [ ] Implementation complete
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] Full test suite green (157/157)
- [ ] Manual CLI/API verification done
- [ ] Lint/type clean
- [ ] Committed with descriptive message
- [ ] Pushed to origin
- [ ] CHANGELOG.md updated

---

The loop repeats. Each turn produces a working, tested, documented increment that could ship.

## Coordination Rule

Agents must respect domain ownership. Cross-domain changes should be
explicit and documented.
