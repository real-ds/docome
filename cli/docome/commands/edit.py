import sys
from pathlib import Path
from typing import Optional, Tuple

import typer
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from packages.pdf_engine import EditorSession, ShapeType, AnnotationType

edit_app = typer.Typer(help="PDF editing operations")
console = Console()


@edit_app.command("add-text")
def add_text(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    page: int = typer.Option(1, "-p", "--page", help="Page number (1-indexed)"),
    x: float = typer.Option(..., "-x", help="X coordinate"),
    y: float = typer.Option(..., "-y", help="Y coordinate"),
    text: str = typer.Option(..., "-t", "--text", help="Text to add"),
    fontsize: float = typer.Option(12.0, "--fontsize", help="Font size"),
    fontname: str = typer.Option("helv", "--fontname", help="Font name (helv, helb, heit, etc.)"),
    color: str = typer.Option("0,0,0", "--color", help="RGB color as r,g,b (0-1 range)"),
):
    """Add text to a PDF page."""
    c = _parse_color(color)
    session = EditorSession(input)
    session.add_text(page, x, y, text, fontsize, fontname, c)
    session.save(output)
    session.close()
    console.print(f"[green]Text added. Saved to: {output}[/green]")


@edit_app.command("delete-text")
def delete_text(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x0: float = typer.Option(..., "--x0", help="Left coordinate"),
    y0: float = typer.Option(..., "--y0", help="Top coordinate"),
    x1: float = typer.Option(..., "--x1", help="Right coordinate"),
    y1: float = typer.Option(..., "--y1", help="Bottom coordinate"),
):
    """Delete content in a rectangular area."""
    session = EditorSession(input)
    session.delete_text(page, x0, y0, x1, y1)
    session.save(output)
    session.close()
    console.print(f"[green]Content deleted. Saved to: {output}[/green]")


@edit_app.command("replace-text")
def replace_text(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x0: float = typer.Option(..., "--x0", help="Left coordinate"),
    y0: float = typer.Option(..., "--y0", help="Top coordinate"),
    x1: float = typer.Option(..., "--x1", help="Right coordinate"),
    y1: float = typer.Option(..., "--y1", help="Bottom coordinate"),
    text: str = typer.Option(..., "-t", "--text", help="Replacement text"),
    fontsize: float = typer.Option(12.0, "--fontsize", help="Font size"),
):
    """Replace content in a rectangular area with new text."""
    session = EditorSession(input)
    session.replace_text(page, x0, y0, x1, y1, text, fontsize)
    session.save(output)
    session.close()
    console.print(f"[green]Text replaced. Saved to: {output}[/green]")


@edit_app.command("add-image")
def add_image(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    image: str = typer.Option(..., "-i", "--image", help="Image file path"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x: float = typer.Option(..., "-x", help="X coordinate"),
    y: float = typer.Option(..., "-y", help="Y coordinate"),
    width: Optional[float] = typer.Option(None, "-w", "--width", help="Width"),
    height: Optional[float] = typer.Option(None, "-h", "--height", help="Height"),
):
    """Add an image to a PDF page."""
    image_data = Path(image).read_bytes()
    session = EditorSession(input)
    session.add_image(page, image_data, x, y, width, height)
    session.save(output)
    session.close()
    console.print(f"[green]Image added. Saved to: {output}[/green]")


@edit_app.command("draw-shape")
def draw_shape(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    shape: ShapeType = typer.Option(..., "-s", "--shape", help="Shape type (rect, circle, line)"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x0: float = typer.Option(..., "--x0", help="Start X"),
    y0: float = typer.Option(..., "--y0", help="Start Y"),
    x1: float = typer.Option(..., "--x1", help="End X"),
    y1: float = typer.Option(..., "--y1", help="End Y"),
    color: str = typer.Option("0,0,0", "--color", help="Stroke RGB color"),
    fill: Optional[str] = typer.Option(None, "--fill", help="Fill RGB color"),
    width: float = typer.Option(1.0, "--width", help="Stroke width"),
):
    """Draw a shape on a PDF page."""
    c = _parse_color(color)
    f = _parse_color(fill) if fill else None
    session = EditorSession(input)
    session.draw_shape(page, shape, x0, y0, x1, y1, c, f, width)
    session.save(output)
    session.close()
    console.print(f"[green]Shape drawn. Saved to: {output}[/green]")


@edit_app.command("annotate")
def annotate(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    annot_type: AnnotationType = typer.Option(..., "-a", "--type", help="Annotation type"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x0: float = typer.Option(..., "--x0", help="Start X"),
    y0: float = typer.Option(..., "--y0", help="Start Y"),
    x1: float = typer.Option(..., "--x1", help="End X"),
    y1: float = typer.Option(..., "--y1", help="End Y"),
    text: str = typer.Option("", "-t", "--text", help="Annotation text (for freetext/sticky)"),
    color: str = typer.Option("1,1,0", "--color", help="Annotation color"),
):
    """Add annotation to a PDF page."""
    c = _parse_color(color)
    session = EditorSession(input)
    session.add_annotation(page, annot_type, x0, y0, x1, y1, text, c)
    session.save(output)
    session.close()
    console.print(f"[green]Annotation added. Saved to: {output}[/green]")


@edit_app.command("move")
def move_element(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x0: float = typer.Option(..., "--x0", help="Region left"),
    y0: float = typer.Option(..., "--y0", help="Region top"),
    x1: float = typer.Option(..., "--x1", help="Region right"),
    y1: float = typer.Option(..., "--y1", help="Region bottom"),
    dx: float = typer.Option(..., "--dx", help="Horizontal offset"),
    dy: float = typer.Option(..., "--dy", help="Vertical offset"),
):
    """Move a region on a PDF page."""
    session = EditorSession(input)
    session.move_element(page, x0, y0, x1, y1, dx, dy)
    session.save(output)
    session.close()
    console.print(f"[green]Element moved. Saved to: {output}[/green]")


@edit_app.command("resize")
def resize_element(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    x0: float = typer.Option(..., "--x0", help="Region left"),
    y0: float = typer.Option(..., "--y0", help="Region top"),
    x1: float = typer.Option(..., "--x1", help="Region right"),
    y1: float = typer.Option(..., "--y1", help="Region bottom"),
    width: float = typer.Option(..., "-w", "--width", help="New width"),
    height: float = typer.Option(..., "-h", "--height", help="New height"),
):
    """Resize a region on a PDF page."""
    session = EditorSession(input)
    session.resize_element(page, x0, y0, x1, y1, width, height)
    session.save(output)
    session.close()
    console.print(f"[green]Element resized. Saved to: {output}[/green]")


def _parse_color(color_str: str) -> Tuple[float, float, float]:
    parts = color_str.split(",")
    if len(parts) != 3:
        raise typer.BadParameter(f"Invalid color format: {color_str}. Use r,g,b")
    return (float(parts[0]), float(parts[1]), float(parts[2]))
