# OCR Engine

Provider abstraction for OCR.

Possible providers:

- Tesseract
- PaddleOCR
- cloud OCR providers

The rest of the application must depend on an OCRProvider interface rather
than a concrete OCR implementation.
