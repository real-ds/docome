import typer
from rich.console import Console

from .commands.pdf import pdf_app
from .commands.convert import convert_app
from .commands.ocr import ocr_app
from .commands.signature import sig_app
from .commands.edit import edit_app
from .commands.thumbnail import pdf_app as thumb_app

app = typer.Typer(help="Docome PDF/document CLI")
console = Console()

app.add_typer(pdf_app, name="pdf")
app.add_typer(convert_app, name="convert")
app.add_typer(ocr_app, name="ocr")
app.add_typer(sig_app, name="sign")
app.add_typer(edit_app, name="edit")
app.add_typer(thumb_app, name="thumbnail")


@app.command()
def version():
    """Show Docome version."""
    console.print("Docome 0.1.0")


if __name__ == "__main__":
    app()
