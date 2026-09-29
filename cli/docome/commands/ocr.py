import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from packages.ocr_engine import OcrEngine

ocr_app = typer.Typer(help="OCR operations")
console = Console()


@ocr_app.command("providers")
def list_providers():
    """List available OCR providers."""
    engine = OcrEngine()
    providers = engine.get_available_providers()
    
    if providers:
        console.print("[green]Available OCR providers:[/green]")
        for p in providers:
            console.print(f"  - {p}")
    else:
        console.print("[yellow]No OCR providers available[/yellow]")
        console.print("[dim]Install pytesseract or easyocr to enable OCR[/dim]")


@ocr_app.command("pdf2searchable")
def pdf_to_searchable(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output PDF file"),
    lang: str = typer.Option("eng", "-l", "--lang", help="Language code (eng, spa, fra, etc.)"),
):
    """Convert scanned PDF to searchable PDF."""
    console.print(f"[blue]Processing OCR on {input}...[/blue]")
    
    try:
        engine = OcrEngine()
        engine.pdf_to_searchable(input, output, lang)
        console.print(f"[green]Searchable PDF saved to: {output}[/green]")
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Install pytesseract or easyocr to enable OCR[/dim]")
        raise typer.Exit(1)


@ocr_app.command("img2text")
def image_to_text(
    input: str = typer.Argument(..., help="Input image file"),
    lang: str = typer.Option("eng", "-l", "--lang", help="Language code"),
):
    """Extract text from image using OCR."""
    console.print(f"[blue]Extracting text from {input}...[/blue]")
    
    try:
        engine = OcrEngine()
        text = engine.extract_text_from_image(input, lang)
        console.print(text)
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Install pytesseract or easyocr to enable OCR[/dim]")
        raise typer.Exit(1)
