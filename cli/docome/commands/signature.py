import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from packages.signature_engine import SignatureEngine

sig_app = typer.Typer(help="E-signature operations")
console = Console()


@sig_app.command("add-signature")
def add_signature(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output PDF file"),
    signature_file: str = typer.Option(..., "-s", "--signature", help="Signature image file (PNG)"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x: float = typer.Option(100, "-x", "--x", help="X coordinate"),
    y: float = typer.Option(100, "-y", "--y", help="Y coordinate"),
    width: Optional[float] = typer.Option(None, "-w", "--width", help="Width"),
    height: Optional[float] = typer.Option(None, "-ht", "--height", help="Height"),
):
    """Add signature image to PDF."""
    console.print(f"[blue]Adding signature to {input}...[/blue]")
    
    engine = SignatureEngine()
    
    with open(signature_file, "rb") as f:
        sig_data = f.read()
    
    engine.add_signature(input, output, sig_data, page, x, y, width, height)
    
    console.print(f"[green]Signature added. Saved to: {output}[/green]")


@sig_app.command("create-typed")
def create_typed_signature(
    name: str = typer.Argument(..., help="Name to create signature from"),
    output: str = typer.Option(..., "-o", "--output", help="Output PNG file"),
    font_size: int = typer.Option(40, "-s", "--font-size", help="Font size"),
):
    """Create typed signature image."""
    console.print(f"[blue]Creating typed signature for: {name}[/blue]")
    
    engine = SignatureEngine()
    sig_data = engine.create_typed_signature(name, font_size)
    
    Path(output).write_bytes(sig_data)
    
    console.print(f"[green]Signature saved to: {output}[/green]")


@sig_app.command("add-field")
def add_signature_field(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output PDF file"),
    field_id: str = typer.Option(..., "-f", "--field-id", help="Field ID"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x: float = typer.Option(100, "-x", "--x", help="X coordinate"),
    y: float = typer.Option(100, "-y", "--y", help="Y coordinate"),
    width: float = typer.Option(200, "-w", "--width", help="Width"),
    height: float = typer.Option(50, "-ht", "--height", help="Height"),
):
    """Add signature field to PDF."""
    console.print(f"[blue]Adding signature field to {input}...[/blue]")
    
    engine = SignatureEngine()
    engine.add_signature_field(input, output, field_id, page, x, y, width, height)
    
    console.print(f"[green]Signature field added. Saved to: {output}[/green]")


@sig_app.command("add-text-field")
def add_text_field(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output PDF file"),
    field_id: str = typer.Option(..., "-f", "--field-id", help="Field ID"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x: float = typer.Option(100, "-x", "--x", help="X coordinate"),
    y: float = typer.Option(100, "-y", "--y", help="Y coordinate"),
    width: float = typer.Option(200, "-w", "--width", help="Width"),
    height: float = typer.Option(30, "-ht", "--height", help="Height"),
    default: Optional[str] = typer.Option(None, "-d", "--default", help="Default value"),
):
    """Add text field to PDF."""
    console.print(f"[blue]Adding text field to {input}...[/blue]")
    
    engine = SignatureEngine()
    engine.add_text_field(input, output, field_id, page, x, y, width, height, default)
    
    console.print(f"[green]Text field added. Saved to: {output}[/green]")


@sig_app.command("add-date-field")
def add_date_field(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output PDF file"),
    field_id: str = typer.Option(..., "-f", "--field-id", help="Field ID"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x: float = typer.Option(100, "-x", "--x", help="X coordinate"),
    y: float = typer.Option(100, "-y", "--y", help="Y coordinate"),
    width: float = typer.Option(150, "-w", "--width", help="Width"),
    height: float = typer.Option(30, "-ht", "--height", help="Height"),
):
    """Add date field to PDF."""
    console.print(f"[blue]Adding date field to {input}...[/blue]")
    
    engine = SignatureEngine()
    engine.add_date_field(input, output, field_id, page, x, y, width, height)
    
    console.print(f"[green]Date field added. Saved to: {output}[/green]")


@sig_app.command("add-checkbox")
def add_checkbox(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output PDF file"),
    field_id: str = typer.Option(..., "-f", "--field-id", help="Field ID"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x: float = typer.Option(100, "-x", "--x", help="X coordinate"),
    y: float = typer.Option(100, "-y", "--y", help="Y coordinate"),
    size: float = typer.Option(20, "-s", "--size", help="Checkbox size"),
    label: Optional[str] = typer.Option(None, "-l", "--label", help="Label"),
):
    """Add checkbox to PDF."""
    console.print(f"[blue]Adding checkbox to {input}...[/blue]")
    
    engine = SignatureEngine()
    engine.add_checkbox(input, output, field_id, page, x, y, size, label)
    
    console.print(f"[green]Checkbox added. Saved to: {output}[/green]")
