# Docome

All-in-one PDF and document processing platform for Windows.

## Features

### PDF Operations
- Merge multiple PDFs
- Split PDF by pages
- Extract/Remove pages
- Rotate pages (90°, 180°, 270°)
- Compress/Optimize PDFs
- View/Edit metadata
- Password protection
- Convert images to PDF
- Convert PDF to images

### Document Conversion
- PDF ↔ DOCX
- PDF ↔ XLSX
- PDF ↔ PPTX
- PDF → Text
- PDF → Markdown
- HTML → PDF

### E-Signatures
- Create typed signatures
- Add signatures to PDFs
- Add text/date fields
- Add checkboxes
- Signature request workflows

### OCR
- Convert scanned PDFs to searchable PDFs
- Extract text from images (requires Tesseract or EasyOCR)

## Downloads

### Windows Executable
Download the standalone Windows executable from the [Releases](https://github.com/yourusername/docome/releases) page.

- **Docome.exe** - Windows GUI Application (no Python required)

## Installation

### Python Package
```bash
pip install docome
```

### Development
```bash
git clone https://github.com/yourusername/docome.git
cd docome
pip install -e ".[dev]"
```

## Usage

### GUI Application
Double-click `Docome.exe` to launch the graphical interface.

### Command Line
```bash
# PDF Operations
docome pdf merge a.pdf b.pdf -o merged.pdf
docome pdf split document.pdf -o output/ -n 1
docome pdf compress document.pdf -o compressed.pdf -l recommended
docome pdf rotate document.pdf -d 90 -o rotated.pdf

# Document Conversion
docome convert pdf2docx input.pdf -o output.docx
docome convert pdf2txt input.pdf -o output.txt

# E-Signatures
docome sign create-typed "John Doe" -o signature.png
docome sign add-signature document.pdf -o signed.pdf -s signature.png

# OCR
docome ocr pdf2searchable scanned.pdf -o output.pdf
```

## Documentation

See the `docs/` folder for detailed documentation:
- [Architecture](docs/Architecture.md)
- [Development Guide](docs/Development%20Guide.md)
- [CLI Reference](docs/CLI.md)
- [Tech Stack](docs/Techstack.md)

## Tech Stack

- **Python 3.12+**
- **PyMuPDF** - PDF operations
- **Pillow** - Image processing
- **python-docx** - DOCX handling
- **Typer** - CLI framework
- **CustomTkinter** - GUI
- **FastAPI** - REST API

## License

MIT License - see [LICENSE](LICENSE) file.

## Contributing

Contributions are welcome! Please read the [Development Guide](docs/Development%20Guide.md) before submitting PRs.

## Support

For issues and feature requests, please open an issue on GitHub.
