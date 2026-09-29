import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from packages.pdf_engine import (
    PdfEngine,
    CompressLevel,
    Metadata,
    PageRange,
    Rotation,
)
from packages.image_engine import ImageEngine

pdf_app = typer.Typer(help="PDF operations")
console = Console()


@pdf_app.command("merge")
def merge(
    inputs: List[str] = typer.Argument(..., help="Input PDF files to merge"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
):
    """Merge multiple PDF files into one."""
    console.print(f"[blue]Merging {len(inputs)} files...[/blue]")
    
    engine = PdfEngine()
    engine.merge(inputs, output)
    
    console.print(f"[green]Merged PDF saved to: {output}[/green]")


@pdf_app.command("split")
def split(
    input: str = typer.Argument(..., help="Input PDF file"),
    output_dir: str = typer.Option(..., "-o", "--output-dir", help="Output directory"),
    pages_per_split: int = typer.Option(1, "-n", "--pages-per-split", help="Number of pages per split"),
):
    """Split PDF into multiple files."""
    console.print(f"[blue]Splitting {input}...[/blue]")
    
    engine = PdfEngine()
    output_files = engine.split(input, output_dir, pages_per_split)
    
    console.print(f"[green]Split into {len(output_files)} files in: {output_dir}[/green]")


@pdf_app.command("extract")
def extract(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    pages: Optional[str] = typer.Option(None, "-p", "--pages", help="Page range (e.g., '1-5' or '1,3,5')"),
):
    """Extract pages from PDF."""
    engine = PdfEngine()
    
    page_range = None
    page_list = None
    
    if pages:
        if "-" in pages:
            start, end = pages.split("-")
            page_range = PageRange(start=int(start), end=int(end))
        else:
            page_list = [int(p) - 1 for p in pages.split(",")]
    
    engine.extract(input, output, pages=page_list, page_range=page_range)
    
    console.print(f"[green]Extracted pages to: {output}[/green]")


@pdf_app.command("remove")
def remove(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    pages: str = typer.Option(..., "-p", "--pages", help="Pages to remove (e.g., '1-5' or '1,3,5')"),
):
    """Remove pages from PDF."""
    engine = PdfEngine()
    
    if "-" in pages:
        start, end = pages.split("-")
        page_range = PageRange(start=int(start), end=int(end))
        page_list = None
    else:
        page_list = [int(p) - 1 for p in pages.split(",")]
        page_range = None
    
    engine.remove(input, output, pages=page_list, page_range=page_range)
    
    console.print(f"[green]Removed pages from PDF. Saved to: {output}[/green]")


@pdf_app.command("rotate")
def rotate(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    degrees: int = typer.Option(90, "-d", "--degrees", help="Rotation degrees (90, 180, 270)"),
    pages: Optional[str] = typer.Option(None, "-p", "--pages", help="Pages to rotate (e.g., '1,3,5')"),
):
    """Rotate PDF pages."""
    rotation_map = {90: Rotation.ROTATE_90, 180: Rotation.ROTATE_180, 270: Rotation.ROTATE_270}
    
    if degrees not in rotation_map:
        console.print("[red]Invalid rotation. Use 90, 180, or 270[/red]")
        raise typer.Exit(1)
    
    engine = PdfEngine()
    page_list = None
    if pages:
        page_list = [int(p) - 1 for p in pages.split(",")]
    
    engine.rotate(input, output, rotation_map[degrees], pages=page_list)
    
    console.print(f"[green]Rotated {degrees}°. Saved to: {output}[/green]")


@pdf_app.command("compress")
def compress(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    level: CompressLevel = typer.Option(CompressLevel.RECOMMENDED, "-l", "--level", help="Compression level"),
):
    """Compress PDF file."""
    console.print(f"[blue]Compressing with {level.value} level...[/blue]")
    
    engine = PdfEngine()
    engine.compress(input, output, level)
    
    original_size = Path(input).stat().st_size
    compressed_size = Path(output).stat().st_size
    ratio = (1 - compressed_size / original_size) * 100
    
    console.print(f"[green]Compressed: {original_size / 1024:.1f}KB -> {compressed_size / 1024:.1f}KB (saved {ratio:.1f}%)[/green]")


@pdf_app.command("metadata")
def metadata(
    input: str = typer.Argument(..., help="Input PDF file"),
    show: bool = typer.Option(True, "-s", "--show", help="Show metadata"),
    title: Optional[str] = typer.Option(None, "--title", help="Set title"),
    author: Optional[str] = typer.Option(None, "--author", help="Set author"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output file (if modifying metadata)"),
):
    """View or modify PDF metadata."""
    engine = PdfEngine()
    
    if show:
        meta = engine.get_metadata(input)
        console.print("[blue]PDF Metadata:[/blue]")
        if meta.title:
            console.print(f"  Title: {meta.title}")
        if meta.author:
            console.print(f"  Author: {meta.author}")
        if meta.subject:
            console.print(f"  Subject: {meta.subject}")
        if meta.creator:
            console.print(f"  Creator: {meta.creator}")
        if meta.producer:
            console.print(f"  Producer: {meta.producer}")
        if meta.keywords:
            console.print(f"  Keywords: {meta.keywords}")
    
    if title or author:
        if not output:
            console.print("[red]Output file required when modifying metadata[/red]")
            raise typer.Exit(1)
        
        meta = Metadata(title=title, author=author)
        engine.set_metadata(input, output, meta)
        console.print(f"[green]Metadata updated. Saved to: {output}[/green]")


@pdf_app.command("protect")
def protect(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    password: str = typer.Option(..., "-p", "--password", help="Password for the PDF"),
):
    """Add password protection to PDF."""
    engine = PdfEngine()
    engine.protect(input, output, password)
    
    console.print(f"[green]Password protected PDF saved to: {output}[/green]")


@pdf_app.command("pages")
def pages(
    input: str = typer.Argument(..., help="Input PDF file"),
):
    """Show page count."""
    engine = PdfEngine()
    count = engine.get_page_count(input)
    console.print(f"[blue]Page count: {count}[/blue]")


@pdf_app.command("img2pdf")
def img2pdf(
    inputs: List[str] = typer.Argument(..., help="Input image files"),
    output: str = typer.Option(..., "-o", "--output", help="Output PDF file"),
):
    """Convert images to PDF."""
    console.print(f"[blue]Converting {len(inputs)} images to PDF...[/blue]")
    
    engine = ImageEngine()
    engine.images_to_pdf(inputs, output)
    
    console.print(f"[green]PDF saved to: {output}[/green]")


@pdf_app.command("pdf2img")
def pdf2img(
    input: str = typer.Argument(..., help="Input PDF file"),
    output_dir: str = typer.Option(..., "-o", "--output-dir", help="Output directory"),
    dpi: int = typer.Option(150, "--dpi", help="Image DPI"),
    fmt: str = typer.Option("PNG", "--format", help="Image format (PNG, JPEG)"),
):
    """Convert PDF to images."""
    console.print(f"[blue]Converting PDF to images...[/blue]")
    
    engine = ImageEngine()
    output_files = engine.pdf_to_images(input, output_dir, dpi, fmt)
    
    console.print(f"[green]Created {len(output_files)} images in: {output_dir}[/green]")
