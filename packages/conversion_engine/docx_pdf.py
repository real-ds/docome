"""DOCX to PDF rendering built on the MuPDF Story layout engine.

The previous implementation created one A4 page per paragraph and drew the
plain text at a fixed offset, so it lost page size, margins, fonts, colors,
alignment, tables, and images, and it never paginated. This module walks the
document body in order and feeds an HTML rendering of it to
``pymupdf.Story``, which performs real reflow, pagination, and font handling.
"""

from __future__ import annotations

import html
import io
from pathlib import Path
from typing import List, Optional, Union

import pymupdf
from docx import Document
from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

# PyMuPDF resolves these to the built-in Base-14 fonts, so no font files are
# needed and rendering works on any machine.
_FONT_STACK = "sans-serif"
_SERIF_STACK = "serif"
_MONO_STACK = "monospace"

_ALIGNMENT = {
    WD_ALIGN_PARAGRAPH.LEFT: "left",
    WD_ALIGN_PARAGRAPH.RIGHT: "right",
    WD_ALIGN_PARAGRAPH.CENTER: "center",
    WD_ALIGN_PARAGRAPH.JUSTIFY: "justify",
}

_HEADING_TAGS = {
    "Title": "h1",
    "Heading 1": "h1",
    "Heading 2": "h2",
    "Heading 3": "h3",
    "Heading 4": "h4",
    "Heading 5": "h5",
    "Heading 6": "h6",
    "Subtitle": "h2",
}


def _iter_body(document: DocxDocument):
    """Yield paragraphs and tables in the order they appear in the body.

    ``Document.paragraphs`` and ``Document.tables`` are separate lists, so
    using either alone silently reorders content that mixes the two.
    """
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def _twips_to_points(value: Optional[int]) -> float:
    return 0.0 if value is None else value / 20.0


def _font_family(name: Optional[str]) -> str:
    lowered = (name or "").lower()
    if "courier" in lowered or "consolas" in lowered or "mono" in lowered:
        return _MONO_STACK
    if "times" in lowered or "georgia" in lowered or "garamond" in lowered or "serif" in lowered:
        return _SERIF_STACK
    return _FONT_STACK


def _points(value: float) -> str:
    """Format a point value without a pointless trailing ``.0``."""
    return f"{value:g}"


def _color_css(run) -> Optional[str]:
    try:
        color = run.font.color
        if color is None or color.type is None or color.rgb is None:
            return None
        rgb = color.rgb
    except (AttributeError, ValueError, TypeError):
        return None
    return f"#{str(rgb).lower()}"


def _run_html(run) -> str:
    text = html.escape(run.text)
    if not text:
        return ""

    style: List[str] = []
    font_name = run.font.name
    if font_name:
        style.append(f"font-family:{_font_family(font_name)}")
    if run.font.size is not None:
        style.append(f"font-size:{_points(run.font.size.pt)}pt")
    if run.bold:
        style.append("font-weight:bold")
    if run.italic:
        style.append("font-style:italic")
    if run.underline:
        style.append("text-decoration:underline")

    color = _color_css(run)
    if color:
        style.append(f"color:{color}")

    if not style:
        return text
    return f'<span style="{";".join(style)}">{text}</span>'


def _paragraph_html(paragraph: Paragraph) -> str:
    tag = _HEADING_TAGS.get(paragraph.style.name or "", "p")
    parts = [_run_html(run) for run in paragraph.runs]
    body = "".join(parts) or html.escape(paragraph.text)

    style: List[str] = []
    alignment = _ALIGNMENT.get(paragraph.alignment)
    if alignment:
        style.append(f"text-align:{alignment}")

    name = paragraph.style.name or ""
    if "List Bullet" in name:
        body = f"&#8226;&nbsp;&nbsp;{body}"
    elif "List Number" in name:
        body = f"1.&nbsp;&nbsp;{body}"

    indent = _left_indent_points(paragraph)
    if indent:
        style.append(f"margin-left:{_points(indent)}pt")

    if not style:
        return f"<{tag}>{body}</{tag}>"
    return f'<{tag} style="{";".join(style)}">{body}</{tag}>'


def _left_indent_points(paragraph: Paragraph) -> float:
    fmt = paragraph.paragraph_format
    value = getattr(fmt, "left_indent", None)
    if value is None:
        return 0.0
    return value.pt


def _cell_background(cell) -> Optional[str]:
    properties = cell._tc.tcPr
    if properties is None:
        return None
    shading = properties.find(qn("w:shd"))
    if shading is None:
        return None
    fill = shading.get(qn("w:fill"))
    if not fill or fill.lower() in {"auto", "ffffff"}:
        return None
    return f"#{fill}"


def _cell_html(cell) -> str:
    parts = [_paragraph_html(paragraph) for paragraph in cell.paragraphs]
    body = "".join(parts) or "&nbsp;"

    style: List[str] = ["border:0.5pt solid #999999", "padding:2pt", "vertical-align:top"]
    background = _cell_background(cell)
    if background:
        style.append(f"background-color:{background}")

    return f'<td style="{";".join(style)}">{body}</td>'


def _table_html(table: Table) -> str:
    rows = []
    for row in table.rows:
        cells = "".join(_cell_html(cell) for cell in row.cells)
        rows.append(f"<tr>{cells}</tr>")
    if not rows:
        return ""
    return f'<table style="border-collapse:collapse">{"".join(rows)}</table>'


def _images_html(document: DocxDocument) -> str:
    """Collect embedded images as data URIs.

    Story renders from a single HTML string, so inline images have to be
    inlined as data URIs rather than referenced from disk.
    """
    parts: List[str] = []
    for part in document.part.package.parts:
        if not part.content_type.startswith("image/"):
            continue
        try:
            blob = part.blob
        except (AttributeError, NotImplementedError):
            continue
        encoded = _encode_image(blob, part.content_type)
        if encoded:
            parts.append(f'<img src="{encoded}"/>')
    return f'<div>{"".join(parts)}</div>' if parts else ""


def _encode_image(blob: bytes, content_type: str) -> Optional[str]:
    import base64

    suffix = content_type.split("/")[-1].replace("jpeg", "jpg")
    return f"data:image/{suffix};base64,{base64.b64encode(blob).decode('ascii')}"


def _first_section(document: DocxDocument):
    return document.sections[0] if document.sections else None


def _page_geometry(document: DocxDocument) -> Tuple[float, float, float, float, float, float]:
    section = _first_section(document)
    if section is None:
        return 595.0, 842.0, 72.0, 72.0, 72.0, 72.0

    width = section.page_width.pt if section.page_width else 595.0
    height = section.page_height.pt if section.page_height else 842.0
    left = section.left_margin.pt if section.left_margin else 72.0
    right = section.right_margin.pt if section.right_margin else 72.0
    top = section.top_margin.pt if section.top_margin else 72.0
    bottom = section.bottom_margin.pt if section.bottom_margin else 72.0
    return width, height, left, top, right, bottom


def docx_to_html(source: Union[str, Path, bytes, DocxDocument]) -> str:
    """Render the DOCX body to an HTML fragment suitable for Story."""
    if isinstance(source, DocxDocument):
        document = source
    elif isinstance(source, bytes):
        document = Document(io.BytesIO(source))
    else:
        document = Document(source)

    blocks: List[str] = []
    for item in _iter_body(document):
        if isinstance(item, Paragraph):
            blocks.append(_paragraph_html(item))
        else:
            blocks.append(_table_html(item))

    images = _images_html(document)
    if images:
        blocks.append(images)

    return f'<div>{"".join(blocks)}</div>'


def docx_to_pdf(
    input_path: Union[str, Path, bytes],
    output_path: Union[str, Path],
) -> None:
    """Render a DOCX file to PDF with real pagination and formatting."""
    if isinstance(input_path, bytes):
        document = Document(io.BytesIO(input_path))
    else:
        document = Document(input_path)

    markup = docx_to_html(document)
    width, height, left, top, right, bottom = _page_geometry(document)

    output = Path(output_path)
    story = pymupdf.Story(html=markup, archive=pymupdf.Archive("."))
    mediabox = pymupdf.Rect(0, 0, width, height)
    where = pymupdf.Rect(left, top, width - right, height - bottom)

    if not _has_area(where):
        raise ValueError(
            f"Page margins leave no printable area ({left}pt, {top}pt, "
            f"{right}pt, {bottom}pt on a {width}x{height}pt page)"
        )

    writer = pymupdf.DocumentWriter(str(output))
    more = True
    while more:
        device = writer.begin_page(mediabox)
        more, filled = story.place(where)
        if more and not _has_area(filled):
            # Content too large for the frame would otherwise loop forever.
            break
        story.draw(device)
        writer.end_page()
    writer.close()


def _has_area(filled) -> bool:
    if isinstance(filled, pymupdf.Rect):
        return filled.width > 0 and filled.height > 0
    x0, y0, x1, y1 = filled
    return (x1 - x0) > 0 and (y1 - y0) > 0
