# Contributing to Docome

Thank you for your interest in contributing to Docome!

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported
2. Create a new issue with:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details

### Suggesting Features

1. Open a new issue with `[Feature Request]` prefix
2. Describe the feature and its use case
3. Explain why this would be beneficial

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests if applicable
5. Ensure tests pass: `pytest tests/`
6. Commit with clear messages
7. Push to your fork
8. Submit a pull request

## Development Setup

```bash
git clone https://github.com/yourusername/docome.git
cd docome
pip install -e ".[dev]"
```

## Code Style

- Use Ruff for linting
- Follow PEP 8
- Add type hints where possible
- Write docstrings for new functions

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_pdf_engine.py
```

## Project Structure

```
docome/
├── apps/              # API application
├── cli/               # CLI interface
├── packages/          # Document processing engines
│   ├── pdf_engine/
│   ├── conversion_engine/
│   ├── image_engine/
│   ├── ocr_engine/
│   └── signature_engine/
├── tests/             # Test suite
└── docs/              # Documentation
```

## Questions?

Open an issue for questions about contributing.
