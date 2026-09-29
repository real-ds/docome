import io
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pymupdf
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Pt, RGBColor
from PIL import Image


@dataclass
class FontInfo:
    name: str
    size: float
    bold: bool
    italic: bool
    color: Tuple[int, int, int]
    font_id: str = ""


@dataclass
class TextBlock:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    font: FontInfo
    page_num: int
    line_num: int = 0


@dataclass
class TableCell:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    row_span: int = 1
    col_span: int = 1


@dataclass
class Table:
    x0: float
    y0: float
    x1: float
    y1: float
    rows: int
    cols: int
    cells: List[List[TableCell]]


@dataclass
class ImageBlock:
    x0: float
    y0: float
    x1: float
    y1: float
    image_data: bytes
    ext: str


@dataclass
class LinkBlock:
    x0: float
    y0: float
    x1: float
    y1: float
    uri: str
    text: str


@dataclass
class PageStructure:
    page_num: int
    width: float
    height: float
    text_blocks: List[TextBlock] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    images: List[ImageBlock] = field(default_factory=list)
    links: List[LinkBlock] = field(default_factory=list)


class FontMapper:
    FONT_ALIASES = {
        "helv": "Arial",
        "helvetica": "Arial",
        "times": "Times New Roman",
        "times-roman": "Times New Roman",
        "courier": "Courier New",
        "symbol": "Symbol",
        "zapfdingbats": "Wingdings",
    }

    @classmethod
    def map_font(cls, pdf_font_name: str) -> str:
        name = pdf_font_name.lower().replace("-", "").replace(" ", "")
        for alias, mapped in cls.FONT_ALIASES.items():
            if alias in name:
                return mapped
        return "Arial"

    @classmethod
    def get_weight(cls, flags: int) -> bool:
        return bool(flags & 2)

    @classmethod
    def get_italic(cls, flags: int) -> bool:
        return bool(flags & 1)


class TextBlockDetector:
    def __init__(self, line_height_tolerance: float = 2.0, char_width_tolerance: float = 1.5):
        self.line_height_tolerance = line_height_tolerance
        self.char_width_tolerance = char_width_tolerance

    def detect_blocks(self, page: pymupdf.Page, page_num: int) -> List[TextBlock]:
        blocks = page.get_text("dict", flags=pymupdf.TEXTFLAGS_DICT)
        text_blocks = []

        for block in blocks.get("blocks", []):
            if block.get("type") != 0:
                continue

            for line in block.get("lines", []):
                line_text = ""
                spans = line.get("spans", [])
                if not spans:
                    continue

                first_span = spans[0]
                font = FontInfo(
                    name=FontMapper.map_font(first_span.get("font", "helv")),
                    size=first_span.get("size", 12),
                    bold=FontMapper.get_weight(first_span.get("flags", 0)),
                    italic=FontMapper.get_italic(first_span.get("flags", 0)),
                    color=self._color_to_rgb(first_span.get("color", 0)),
                    font_id=first_span.get("font", ""),
                )

                x0 = line.get("bbox", [0, 0, 0, 0])[0]
                y0 = line.get("bbox", [0, 0, 0, 0])[1]
                x1 = line.get("bbox", [0, 0, 0, 0])[2]
                y1 = line.get("bbox", [0, 0, 0, 0])[3]

                for span in spans:
                    line_text += span.get("text", "")

                if line_text.strip():
                    text_blocks.append(TextBlock(
                        x0=x0, y0=y0, x1=x1, y1=y1,
                        text=line_text.strip(),
                        font=font,
                        page_num=page_num,
                    ))

        return self._merge_lines(text_blocks)

    def _merge_lines(self, blocks: List[TextBlock]) -> List[TextBlock]:
        if not blocks:
            return []

        blocks.sort(key=lambda b: (b.page_num, b.y0, b.x0))
        merged = []
        current = blocks[0]

        for block in blocks[1:]:
            same_font = (current.font.name == block.font.name and
                        abs(current.font.size - block.font.size) < 0.5 and
                        current.font.bold == block.font.bold and
                        current.font.italic == block.font.italic and
                        current.font.color == block.font.color)

            vertical_gap = block.y0 - current.y1
            horizontal_overlap = min(current.x1, block.x1) - max(current.x0, block.x0)

            if (same_font and current.page_num == block.page_num and
                vertical_gap < self.line_height_tolerance and
                horizontal_overlap > 0):
                current.text += " " + block.text
                current.y1 = max(current.y1, block.y1)
                current.x1 = max(current.x1, block.x1)
            else:
                merged.append(current)
                current = block

        merged.append(current)
        return merged

    def _color_to_rgb(self, color: int) -> Tuple[int, int, int]:
        if color == 0:
            return (0, 0, 0)
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return (r, g, b)


class TableDetector:
    def __init__(self, min_rows: int = 2, min_cols: int = 2, cell_padding: float = 3.0):
        self.min_rows = min_rows
        self.min_cols = min_cols
        self.cell_padding = cell_padding

    def detect_tables(self, page: pymupdf.Page) -> List[Table]:
        tables = []
        drawings = page.get_drawings()
        lines = self._extract_lines(drawings)
        h_lines, v_lines = self._separate_lines(lines)

        intersections = self._find_intersections(h_lines, v_lines)
        if len(intersections) < 4:
            return []

        grids = self._find_grids(intersections)
        for grid in grids:
            table = self._build_table(grid, page)
            if table.rows >= self.min_rows and table.cols >= self.min_cols:
                tables.append(table)

        return tables

    def _extract_lines(self, drawings) -> List[Tuple[float, float, float, float]]:
        lines = []
        for drawing in drawings:
            for item in drawing.get("items", []):
                if item[0] == "l":
                    x0, y0 = item[1]
                    x1, y1 = item[2]
                    lines.append((x0, y0, x1, y1))
        return lines

    def _separate_lines(self, lines) -> Tuple[List, List]:
        h_lines, v_lines = [], []
        for x0, y0, x1, y1 in lines:
            if abs(y1 - y0) < 2:
                h_lines.append((x0, y0, x1, y1))
            elif abs(x1 - x0) < 2:
                v_lines.append((x0, y0, x1, y1))
        return h_lines, v_lines

    def _find_intersections(self, h_lines, v_lines) -> List[Tuple[float, float]]:
        intersections = []
        for hx0, hy0, hx1, hy1 in h_lines:
            for vx0, vy0, vx1, vy1 in v_lines:
                if hx0 <= vx0 <= hx1 and vy0 <= hy0 <= vy1:
                    intersections.append((vx0, hy0))
        return intersections

    def _find_grids(self, intersections) -> List[dict]:
        if len(intersections) < 4:
            return []

        intersections.sort(key=lambda p: (p[1], p[0]))
        grids = []
        used = set()

        for i, (x, y) in enumerate(intersections):
            if i in used:
                continue
            grid = self._expand_grid(intersections, i, used)
            if grid:
                grids.append(grid)

        return grids

    def _expand_grid(self, intersections, start_idx, used) -> Optional[dict]:
        x, y = intersections[start_idx]
        same_row = [i for i, (xi, yi) in enumerate(intersections)
                    if abs(yi - y) < 5 and i not in used]
        same_col = [i for i, (xi, yi) in enumerate(intersections)
                    if abs(xi - x) < 5 and i not in used]

        if len(same_row) >= 2 and len(same_col) >= 2:
            for idx in same_row + same_col:
                used.add(idx)
            return {"top_left": (x, y), "row_indices": same_row, "col_indices": same_col}
        return None

    def _build_table(self, grid, page) -> Table:
        rows = len(grid["row_indices"])
        cols = len(grid["col_indices"])
        return Table(x0=0, y0=0, x1=0, y1=0, rows=rows, cols=cols, cells=[])


class ImageExtractor:
    def extract_images(self, page: pymupdf.Page, page_num: int) -> List[ImageBlock]:
        images = []
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                base_image = page.parent.extract_image(xref)
                if base_image:
                    img_data = base_image["image"]
                    ext = base_image.get("ext", "png")
                    bbox = page.get_image_bbox(img)
                    if bbox:
                        images.append(ImageBlock(
                            x0=bbox.x0, y0=bbox.y0,
                            x1=bbox.x1, y1=bbox.y1,
                            image_data=img_data, ext=ext
                        ))
            except Exception:
                pass
        return images


class LinkExtractor:
    def extract_links(self, page: pymupdf.Page) -> List[LinkBlock]:
        links = []
        for link in page.get_links():
            if link.get("kind") == 2:
                bbox = link.get("from", pymupdf.Rect(0, 0, 0, 0))
                links.append(LinkBlock(
                    x0=bbox.x0, y0=bbox.y0, x1=bbox.x1, y1=bbox.y1,
                    uri=link.get("uri", ""), text=""
                ))
        return links


class DocxBuilder:
    def __init__(self, doc: Document):
        self.doc = doc
        self._style_cache = {}

    def add_paragraph(self, block: TextBlock) -> None:
        p = self.doc.add_paragraph()
        run = p.add_run(block.text)
        self._apply_font(run, block.font)

        alignment = self._detect_alignment(block)
        if alignment:
            p.alignment = alignment

    def _apply_font(self, run, font: FontInfo) -> None:
        run.font.name = font.name
        run.font.size = Pt(font.size)
        run.font.bold = font.bold
        run.font.italic = font.italic
        run.font.color.rgb = RGBColor(*font.color)

    def _detect_alignment(self, block: TextBlock) -> Optional[WD_ALIGN_PARAGRAPH]:
        page_center = 300
        block_center = (block.x0 + block.x1) / 2
        if abs(block_center - page_center) < 50:
            return WD_ALIGN_PARAGRAPH.CENTER
        elif block.x0 < 100:
            return WD_ALIGN_PARAGRAPH.LEFT
        return None

    def add_table(self, table: Table) -> None:
        if not table.cells or table.rows < 1 or table.cols < 1:
            return
        doc_table = self.doc.add_table(rows=table.rows, cols=table.cols)
        doc_table.style = "Table Grid"
        for row_idx, row in enumerate(table.cells):
            for col_idx, cell in enumerate(row):
                if col_idx < len(doc_table.rows[row_idx].cells):
                    doc_table.rows[row_idx].cells[col_idx].text = cell.text

    def add_image(self, img: ImageBlock) -> None:
        try:
            img_stream = io.BytesIO(img.image_data)
            self.doc.add_picture(img_stream, width=Cm((img.x1 - img.x0) / 28.35))
        except Exception:
            pass

    def add_link(self, link: LinkBlock, paragraph) -> None:
        run = paragraph.add_run(link.text)
        run.hyperlink = link.uri


class HighFidelityPdfToDocx:
    def __init__(self):
        self.text_detector = TextBlockDetector()
        self.table_detector = TableDetector()
        self.image_extractor = ImageExtractor()
        self.link_extractor = LinkExtractor()

    def convert(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
    ) -> None:
        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        doc = Document()
        builder = DocxBuilder(doc)

        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            structure = self._analyze_page(page, page_num)

            for block in structure.text_blocks:
                builder.add_paragraph(block)

            for table in structure.tables:
                builder.add_table(table)

            for img in structure.images:
                builder.add_image(img)

            if page_num < len(pdf_doc) - 1:
                doc.add_page_break()

        doc.save(output_path)
        pdf_doc.close()

    def _analyze_page(self, page: pymupdf.Page, page_num: int) -> PageStructure:
        width = page.rect.width
        height = page.rect.height

        return PageStructure(
            page_num=page_num,
            width=width,
            height=height,
            text_blocks=self.text_detector.detect_blocks(page, page_num),
            tables=self.table_detector.detect_tables(page),
            images=self.image_extractor.extract_images(page, page_num),
            links=self.link_extractor.extract_links(page),
        )


def pdf_to_docx_hq(
    input_path: Union[str, Path, bytes],
    output_path: Union[str, Path],
) -> None:
    converter = HighFidelityPdfToDocx()
    converter.convert(input_path, output_path)