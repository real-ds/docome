import json
import sys
from pathlib import Path
from typing import Optional, Tuple

import typer
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from packages.pdf_engine import (
    AnnotationType,
    EditPlan,
    EditPlanError,
    EditPlanExecutor,
    EditorSession,
    ElementKind,
    ShapeType,
    apply_edit_plan,
)

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


@edit_app.command("apply")
def apply_plan(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    plan: str = typer.Option(..., "--plan", help="Path to a JSON edit plan"),
    as_json: bool = typer.Option(False, "--json", help="Print the result as JSON"),
):
    """Apply a multi-step JSON edit plan in a single session."""
    try:
        edit_plan = EditPlan.from_file(plan)
        result = apply_edit_plan(input, output, edit_plan)
    except EditPlanError as error:
        console.print(f"[red]Edit plan failed: {error}[/red]")
        raise typer.Exit(code=1)
    except OSError as error:
        console.print(f"[red]Cannot read plan: {error}[/red]")
        raise typer.Exit(code=1)

    if as_json:
        console.print_json(json.dumps(result.as_dict()))
        return

    console.print(f"[green]Applied {result.operation_count} operation(s). Saved to: {output}[/green]")


@edit_app.command("undo")
def undo_operations(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file path"),
    times: int = typer.Option(1, "--times", help="Number of steps to undo"),
):
    """Reopen a PDF and undo the last operations from a saved edit plan."""
    operations = [{"action": "undo", "times": times}]
    try:
        result = apply_edit_plan(input, output, operations)
    except EditPlanError as error:
        console.print(f"[red]Undo failed: {error}[/red]")
        raise typer.Exit(code=1)
    console.print(f"[green]Undid {times} step(s). Saved to: {output}[/green]")


@edit_app.command("actions")
def list_actions():
    """List every action an edit plan can use."""
    table = Table(title="Edit plan actions", show_lines=True)
    table.add_column("Action")
    for action in EditPlanExecutor().available_actions():
        table.add_row(action)
    console.print(table)


@edit_app.command("elements")
def list_elements(
    input: str = typer.Argument(..., help="Input PDF file"),
    page: Optional[int] = typer.Option(None, "--page", "-p", help="Limit to one page"),
    kind: Optional[str] = typer.Option(
        None, "--kind", "-k", help="Filter by kind: text, image, drawing, annotation"
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON instead of a table"),
):
    """List the addressable elements of a PDF, so edits can target them."""
    kinds = None
    if kind:
        try:
            kinds = [ElementKind(kind.lower())]
        except ValueError:
            console.print(f"[red]Unknown kind: {kind}[/red]")
            raise typer.Exit(code=1)

    try:
        with EditorSession(input) as session:
            found = session.list_elements(page=page, kinds=kinds)
    except (ValueError, OSError) as error:
        console.print(f"[red]Could not read {input}: {error}[/red]")
        raise typer.Exit(code=1)

    if not found:
        console.print("[yellow]No elements found.[/yellow]")
        return

    if as_json:
        console.print_json(json.dumps([element.to_dict() for element in found]))
        return

    table = Table(title=f"Elements in {input}", show_lines=True)
    for column in ("ID", "Page", "Kind", "Rect", "Text"):
        table.add_column(column)
    for element in found:
        rect = element.rect
        preview = (element.text or "").strip().replace("\n", " ")
        if len(preview) > 40:
            preview = preview[:37] + "..."
        table.add_row(
            element.id,
            str(element.page),
            element.kind.value,
            f"{rect.x0:.0f},{rect.y0:.0f},{rect.x1:.0f},{rect.y1:.0f}",
            preview,
        )
    console.print(table)


@edit_app.command("pick")
def pick_element(
    input: str = typer.Argument(..., help="Input PDF file"),
    x: float = typer.Option(..., "--x", help="X coordinate"),
    y: float = typer.Option(..., "--y", help="Y coordinate"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON instead of a table"),
):
    """Show what sits under a point, topmost first."""
    try:
        with EditorSession(input) as session:
            hits = session.find_element(page, x, y)
    except (ValueError, OSError) as error:
        console.print(f"[red]Could not read {input}: {error}[/red]")
        raise typer.Exit(code=1)

    if not hits:
        console.print("[yellow]Nothing at that point.[/yellow]")
        return

    if as_json:
        console.print_json(json.dumps([element.to_dict() for element in hits]))
        return

    table = Table(title=f"Elements at ({x:g}, {y:g}) on page {page}", show_lines=True)
    for column in ("ID", "Kind", "Rect", "Text"):
        table.add_column(column)
    for element in hits:
        rect = element.rect
        preview = (element.text or "").strip().replace("\n", " ")
        table.add_row(
            element.id,
            element.kind.value,
            f"{rect.x0:.0f},{rect.y0:.0f},{rect.x1:.0f},{rect.y1:.0f}",
            preview[:50],
        )
    console.print(table)
