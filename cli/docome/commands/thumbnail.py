import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from packages.pdf_engine import render_pages, thumbnail_size
from packages.pdf_engine.thumbnails import MAX_DPI, MIN_DPI

pdf_app = typer.Typer(help="PDF page operations")
console = Console()

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


@pdf_app.command("thumbnail")
def thumbnail(
    input: str = typer.Argument(..., help="Input PDF file"),
    output: str = typer.Option(..., "-o", "--output", help="Output file or directory"),
    pages: Optional[str] = typer.Option(
        None, "--pages", help="Comma-separated page numbers (default: all)"
    ),
    dpi: int = typer.Option(MIN_DPI, "--dpi", help=f"Resolution between {MIN_DPI} and {MAX_DPI}"),
    image_format: str = typer.Option("png", "--format", help="png, jpeg, or webp"),
):
    """Render page previews to image files."""
    try:
        wanted = _parse_pages(pages)
        images = render_pages(input, pages=wanted, dpi=dpi, image_format=image_format)
    except ValueError as error:
        console.print(f"[red]Thumbnail failed: {error}[/red]")
        raise typer.Exit(code=1)
    except OSError as error:
        console.print(f"[red]Could not read {input}: {error}[/red]")
        raise typer.Exit(code=1)

    if not images:
        console.print("[yellow]No pages to render.[/yellow]")
        return

    target = Path(output)
    looks_like_file = target.suffix.lower() in _IMAGE_SUFFIXES

    if looks_like_file and len(images) > 1:
        console.print(
            f"[red]{len(images)} pages were rendered but {target} looks like a single "
            f"image file. Pass a directory instead.[/red]"
        )
        raise typer.Exit(code=1)

    if looks_like_file:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(images[0].data)
        console.print(
            f"[green]Wrote {images[0].width}x{images[0].height} {images[0].media_type} "
            f"to {target}[/green]"
        )
        return

    target.mkdir(parents=True, exist_ok=True)
    written = []
    for image in images:
        path = target / f"{Path(input).stem}-p{image.page}.{image_format.lower()}"
        path.write_bytes(image.data)
        written.append(path)
    console.print(
        f"[green]Wrote {len(written)} image(s) to {target}:[/green] "
        + ", ".join(item.name for item in written)
    )


@pdf_app.command("sizes")
def page_sizes(
    input: str = typer.Argument(..., help="Input PDF file"),
    max_dimension: int = typer.Option(240, "--max", help="Thumbnail bounding box in points"),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON instead of a table"),
):
    """Show the fitted thumbnail size of every page."""
    try:
        sizes = thumbnail_size(input, max_dimension)
    except (ValueError, OSError) as error:
        console.print(f"[red]Could not read {input}: {error}[/red]")
        raise typer.Exit(code=1)

    if as_json:
        console.print_json(
            json.dumps(
                [{"page": page, "width": width, "height": height} for page, (width, height) in sizes]
            )
        )
        return

    table = Table(title=f"Thumbnail sizes for {input}", show_lines=True)
    for column in ("Page", "Width", "Height"):
        table.add_column(column)
    for page, (width, height) in sizes:
        table.add_row(str(page), str(width), str(height))
    console.print(table)


def _parse_pages(pages: Optional[str]) -> Optional[List[int]]:
    if not pages:
        return None
    try:
        return [int(part) for part in pages.split(",") if part.strip()]
    except ValueError as error:
        raise ValueError("pages must be comma-separated page numbers") from error
