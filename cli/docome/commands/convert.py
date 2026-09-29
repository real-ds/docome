import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from packages.conversion_engine import ConversionEngine, pdf_to_docx_hq

convert_app = typer.Typer(help="Document conversion operations")
console = Console()


@convert_app.command("docx2pdf")
def docx2pdf(
    input: str = typer.Argument(..., help="Input DOCX file"),
    output: str = typer.Option(..., "-o", "--output", help="Output PDF file"),
):
    """Convert DOCX to PDF."""
    console.print(f"[blue]Converting {input} to PDF...[/blue]")
    
    engine = ConversionEngine()
    engine.docx_to_pdf(input, output)
    
    console.print(f"[green]PDF saved to: {output}[/green]")


@convert_app.command("pdf2docx")
def pdf2docx(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output DOCX file"),
):
    """Convert PDF to DOCX."""
    console.print(f"[blue]Converting {input} to DOCX...[/blue]")
    
    engine = ConversionEngine()
    engine.pdf_to_docx(input, output)
    
    console.print(f"[green]DOCX saved to: {output}[/green]")


@convert_app.command("pdf2docx-hq")
def pdf2docx_hq_cmd(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output DOCX file"),
):
    """Convert PDF to DOCX with high-fidelity reconstruction."""
    console.print(f"[blue]Converting {input} to DOCX (high fidelity)...[/blue]")
    
    pdf_to_docx_hq(input, output)
    
    console.print(f"[green]High-fidelity DOCX saved to: {output}[/green]")


@convert_app.command("xlsx2pdf")
def xlsx2pdf(
    input: str = typer.Argument(..., help="Input XLSX file"),
    output: str = typer.Option(..., "-o", "--output", help="Output PDF file"),
):
    """Convert XLSX to PDF."""
    console.print(f"[blue]Converting {input} to PDF...[/blue]")
    
    engine = ConversionEngine()
    engine.xlsx_to_pdf(input, output)
    
    console.print(f"[green]PDF saved to: {output}[/green]")


@convert_app.command("pdf2xlsx")
def pdf2xlsx(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output XLSX file"),
):
    """Convert PDF to XLSX."""
    console.print(f"[blue]Converting {input} to XLSX...[/blue]")
    
    engine = ConversionEngine()
    engine.pdf_to_xlsx(input, output)
    
    console.print(f"[green]XLSX saved to: {output}[/green]")


@convert_app.command("pptx2pdf")
def pptx2pdf(
    input: str = typer.Argument(..., help="Input PPTX file"),
    output: str = typer.Option(..., "-o", "--output", help="Output PDF file"),
):
    """Convert PPTX to PDF."""
    console.print(f"[blue]Converting {input} to PDF...[/blue]")
    
    engine = ConversionEngine()
    engine.pptx_to_pdf(input, output)
    
    console.print(f"[green]PDF saved to: {output}[/green]")


@convert_app.command("pdf2pptx")
def pdf2pptx(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output PPTX file"),
):
    """Convert PDF to PPTX."""
    console.print(f"[blue]Converting {input} to PPTX...[/blue]")
    
    engine = ConversionEngine()
    engine.pdf_to_pptx(input, output)
    
    console.print(f"[green]PPTX saved to: {output}[/green]")


@convert_app.command("html2pdf")
def html2pdf(
    input: str = typer.Argument(..., help="Input HTML file or URL"),
    output: str = typer.Option(..., "-o", "--output", help="Output PDF file"),
):
    """Convert HTML to PDF."""
    console.print(f"[blue]Converting {input} to PDF...[/blue]")
    
    engine = ConversionEngine()
    engine.html_to_pdf(input, output)
    
    console.print(f"[green]PDF saved to: {output}[/green]")


@convert_app.command("pdf2txt")
def pdf2txt(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output text file (optional)"),
):
    """Convert PDF to plain text."""
    console.print(f"[blue]Converting {input} to text...[/blue]")
    
    engine = ConversionEngine()
    text = engine.pdf_to_text(input, output)
    
    if output:
        console.print(f"[green]Text saved to: {output}[/green]")
    else:
        console.print(text[:500] + "..." if len(text) > 500 else text)


@convert_app.command("pdf2md")
def pdf2md(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output markdown file (optional)"),
):
    """Convert PDF to Markdown."""
    console.print(f"[blue]Converting {input} to Markdown...[/blue]")
    
    engine = ConversionEngine()
    md = engine.pdf_to_markdown(input, output)
    
    if output:
        console.print(f"[green]Markdown saved to: {output}[/green]")
    else:
        console.print(md[:500] + "..." if len(md) > 500 else md)
