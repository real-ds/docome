import sys
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich import box

from .commands.pdf import pdf_app
from .commands.convert import convert_app
from .commands.ocr import ocr_app
from .commands.signature import sig_app
from .commands.edit import edit_app
from .commands.thumbnail import pdf_app as thumb_app

app = typer.Typer(help="Docome PDF/document CLI")
console = Console()

# Add version option
app.add_typer(pdf_app, name="pdf")
app.add_typer(convert_app, name="convert")
app.add_typer(ocr_app, name="ocr")
app.add_typer(sig_app, name="sign")
app.add_typer(edit_app, name="edit")
app.add_typer(thumb_app, name="thumbnail")

# Detect if running in interactive terminal
INTERACTIVE = sys.stdout.isatty() and sys.stdin.isatty()

# Track command history for interactive mode
command_history: list = []
history_index = -1


@app.command()
def version():
    """Show the version."""
    console.print("Docome 0.1.0")


@app.command()
def interactive():
    """Start interactive terminal mode.

    This command is only available in interactive mode.
    Run `docome` without arguments to enter the interactive terminal.
    """
    if not INTERACTIVE:
        console.print("[red]Error: Interactive mode requires a terminal.[/red]")
        raise typer.Exit(code=1)

    # Show startup banner
    show_startup_banner()

    # Main interaction loop
    while True:
        try:
            # Get user input
            user_input = Prompt.ask("docome > ")

            # Handle empty input
            if not user_input.strip():
                continue

            # Handle exit/quit
            if user_input.strip().lower() in ("/exit", "/quit", "/q", "exit", "quit"):
                console.print("[dim]Goodbye![/dim]")
                break

            # Handle / commands
            if user_input.strip().startswith("/"):
                cmd = user_input.strip()[1:].strip()
                handle_slash_command(cmd)
                continue

            # Handle regular commands - pass to typer processing
            process_regular_command(user_input)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break


def show_startup_banner():
    """Display the Docome startup banner."""
    banner = r"""
  ____   ___   ____   ___   __  __  _____
 |  _ \ / _ \ / ___| / _ \ |  \/  || ____|
 | | | | | |   | |   | | | || |\/| ||  _|
 | |_| | |_| | |___ | |_| || |  | || |___
 |____/ \___/ \____| \___/ |_|  |_||_____|

"""
    table = Table(
        box=box.HEAVY,
        style="white",
        padding=(0, 1),
    )
    table.add_row(f"[bold white]{banner.strip()}[/bold white]")
    table.add_row("    DOCUMENT CONVERSION TOOL     Open Source")
    table.add_row("Document conversion. Right from your terminal.")
    table.add_row("    v0.1.0  ·  Type /help to get started")
    table.add_row("─" * 50)

    console.print(table)


def handle_slash_command(cmd: str):
    """Handle / prefixed commands for interactive features."""
    parts = cmd.split()
    command = parts[0].lower() if parts else ""

    if command == "help":
        show_interactive_help()
    elif command == "formats":
        show_formats()
    elif command == "history":
        show_history()
    elif command == "clear":
        console.clear()
    elif command in ("exit", "quit", "q"):
        console.print("[dim]Goodbye![/dim]")
        raise typer.Exit(code=0)
    elif command == "convert" and len(parts) > 1:
        # Start conversion workflow
        start_conversion_workflow(" ".join(parts[1:]))
    else:
        console.print(f"[yellow]Unknown command: /{command}[/yellow]")
        console.print("Type /help to see available commands.")


def show_interactive_help():
    """Show help in interactive mode."""
    table = Table(box=box.SIMPLE, style="white")
    table.add_column("Command", style="white", no_wrap=True)
    table.add_column("Description", style="muted gray")

    commands_help = [
        ("/help", "Show available commands"),
        ("/formats", "View supported formats"),
        ("/history", "View conversion history"),
        ("/clear", "Clear the screen"),
        ("/exit or /quit", "Exit Docome"),
        ("/convert <type>", "Start conversion workflow"),
    ]

    for cmd, desc in commands_help:
        table.add_row(cmd, desc)

    console.print(table)


def show_formats():
    """Show supported formats."""
    table = Table(box=box.SIMPLE, style="white")
    table.add_column("Source", style="white")
    table.add_column("Target Formats", style="muted gray")

    formats = [
        ("PDF", "DOCX, DOCX-hq, XLSX, PPTX, TXT, MD"),
        ("DOCX", "PDF"),
        ("PNG/JPG", "JPEG, PNG, WebP, BMP"),
        ("Image to PDF", "Single or multiple images"),
    ]

    for source, targets in formats:
        table.add_row(source, targets)

    console.print(table)


def show_history():
    """Show conversion history."""
    table = Table(box=box.SIMPLE, style="white")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Input", style="white", min_width=20)
    table.add_column("Output", style="white", min_width=20)
    table.add_column("Status", style="green", min_width=12)

    if not command_history:
        table.add_row("[italic]No conversions yet[/italic]", "", "", "")
    else:
        # Show last 10 conversions
        recent = command_history[-10:]
        for i, hist in enumerate(reversed(recent)):
            table.add_row(
                str(i + 1),
                hist[:25] + ("..." if len(hist) > 25 else ""),
                hist[:25] + ("..." if len(hist) > 25 else ""),
                "[green]Completed[/green]",
            )

    console.print(table)


def show_settings():
    """Show settings."""
    table = Table(box=box.SIMPLE, style="white")
    table.add_column("Setting", style="white")
    table.add_column("Value", style="muted gray")

    settings = [
        ("Application", "Docome 0.1.0"),
        ("Mode", "Interactive Terminal"),
    ]

    for setting, value in settings:
        table.add_row(setting, value)

    console.print(table)


def start_conversion_workflow(input_spec: str):
    """Start the conversion workflow from interactive mode."""
    console.print(f"\n[blue]Starting conversion: {input_spec}[/blue]")

    # Check if it's "source into dest" format
    if " into " in input_spec.lower():
        parts = input_spec.lower().split(" into ")
        source = parts[0].strip()
        dest = parts[1].strip()
        console.print(f"[green]Source: {source}[/green]")
        console.print(f"[green]Destination: {dest}[/green]")

        # Auto-detect conversion type from extensions
        from pathlib import Path

        src_ext = Path(source).suffix.lower()
        dst_ext = Path(dest).suffix.lower()

        conversion_map = {
            (".png", ".pdf"): "img2pdf",
            (".jpg", ".pdf"): "img2pdf",
            (".jpeg", ".pdf"): "img2pdf",
            (".pdf", ".docx"): "pdf2docx",
            (".pdf", ".docx-hq"): "pdf2docx-hq",
        }

        conv_key = (src_ext, dst_ext)
        if conv_key in conversion_map:
            conv_type = conversion_map[conv_key]
            console.print(f"[green]Conversion type: {conv_type}[/green]")
        else:
            console.print("[red]Unsupported conversion - using existing format[/red]")
    else:
        # Use existing flag-based format
        console.print(f"[green]Using format specification: {input_spec}[/green]")


def process_regular_command(user_input: str):
    """Process a regular (non-slash) command through Typer."""
    parts = user_input.strip().split()

    if not parts:
        return

    cmd_name = parts[0].lower()

    # Map known command names to help output
    if cmd_name == "version":
        console.print("Docome 0.1.0")
    elif cmd_name == "help" or cmd_name == "h":
        console.print(
            """
Available top-level commands:
  docome pdf        - PDF operations (merge, split, etc.)
  docome convert    - Document and image conversion
  docome ocr        - OCR operations
  docome sign       - E-signature operations
  docome edit       - PDF editing operations
  docome thumbnail  - PDF page operations
  docome version    - Show version information
  docome --help     - Full command documentation
"""
        )
    elif cmd_name in ["pdf", "convert", "ocr", "sign", "edit", "thumbnail"]:
        remaining = " ".join(parts[1:]) if len(parts) > 1 else ""
        console.print(f"[dim> Use: docome {cmd_name} {remaining}[/dim>")
        console.print("[yellow]This runs in non-interactive CLI mode.[/yellow]")
    else:
        console.print(f"[dim> docome {user_input}[/dim>")
        console.print("[dim> Command processed by Typer CLI[/dim>")


if __name__ == "__main__":
    # If running in interactive mode and no args provided, start interactive
    if INTERACTIVE and len(sys.argv) == 1:
        # Don't auto-invoke - let the interactive command handle it
        pass

    app()