import copy
import io
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pymupdf


class ShapeType(str, Enum):
    RECT = "rect"
    CIRCLE = "circle"
    LINE = "line"


class AnnotationType(str, Enum):
    HIGHLIGHT = "highlight"
    UNDERLINE = "underline"
    STRIKEOUT = "strikeout"
    FREETEXT = "freetext"
    STICKY = "sticky"


@dataclass
class EditorOperation:
    op_type: str
    page: int
    params: dict


class EditorSession:
    def __init__(self, input_path: Union[str, Path, bytes]):
        if isinstance(input_path, bytes):
            self.doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            self.doc = pymupdf.open(input_path)

        self._snapshots: List[bytes] = []
        self._position: int = -1
        self._save_snapshot()

    @property
    def undo_depth(self) -> int:
        return self._position

    @property
    def redo_depth(self) -> int:
        return max(0, len(self._snapshots) - 1 - self._position)

    @property
    def page_count(self) -> int:
        return len(self.doc)

    def _save_snapshot(self):
        buf = io.BytesIO()
        self.doc.save(buf)
        self._snapshots.append(buf.getvalue())
        self._position = len(self._snapshots) - 1

    def _truncate_and_save(self):
        # Truncate snapshots after current position, then add new snapshot
        self._snapshots = self._snapshots[:self._position + 1]
        self._save_snapshot()

    def undo(self) -> bool:
        if self._position <= 0:
            return False
        self._position -= 1
        state = self._snapshots[self._position]
        self.doc.close()
        self.doc = pymupdf.open(stream=state, filetype="pdf")
        return True

    def redo(self) -> bool:
        if self._position >= len(self._snapshots) - 1:
            return False
        self._position += 1
        state = self._snapshots[self._position]
        self.doc.close()
        self.doc = pymupdf.open(stream=state, filetype="pdf")
        return True

    def add_text(
        self,
        page: int,
        x: float,
        y: float,
        text: str,
        fontsize: float = 12.0,
        fontname: str = "helv",
        color: Tuple[float, float, float] = (0, 0, 0),
    ):
        if page < 1 or page > len(self.doc):
            raise ValueError(f"Invalid page: {page}")
        pdf_page = self.doc[page - 1]
        pdf_page.insert_text((x, y), text, fontsize=fontsize, fontname=fontname, color=color)
        self._truncate_and_save()

    def delete_text(
        self,
        page: int,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ):
        if page < 1 or page > len(self.doc):
            raise ValueError(f"Invalid page: {page}")
        pdf_page = self.doc[page - 1]
        rect = pymupdf.Rect(x0, y0, x1, y1)
        pdf_page.add_redact_annot(rect, fill=(1, 1, 1))
        pdf_page.apply_redactions(
            images=pymupdf.PDF_REDACT_IMAGE_NONE,
            graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
            text=pymupdf.PDF_REDACT_TEXT_REMOVE,
        )
        self._truncate_and_save()

    def replace_text(
        self,
        page: int,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        new_text: str,
        fontsize: float = 12.0,
        fontname: str = "helv",
        color: Tuple[float, float, float] = (0, 0, 0),
    ):
        self.delete_text(page, x0, y0, x1, y1)
        self.add_text(page, x0, y1 - 2, new_text, fontsize, fontname, color)
        self._truncate_and_save()

    def add_image(
        self,
        page: int,
        image_data: bytes,
        x: float,
        y: float,
        width: Optional[float] = None,
        height: Optional[float] = None,
    ):
        if page < 1 or page > len(self.doc):
            raise ValueError(f"Invalid page: {page}")
        pdf_page = self.doc[page - 1]

        img_doc = pymupdf.open(stream=image_data, filetype="png")
        img_page = img_doc[0]
        img_rect = img_page.rect

        if width and height:
            target_rect = pymupdf.Rect(x, y, x + width, y + height)
        elif width:
            ratio = img_rect.height / img_rect.width
            target_rect = pymupdf.Rect(x, y, x + width, y + width * ratio)
        elif height:
            ratio = img_rect.width / img_rect.height
            target_rect = pymupdf.Rect(x, y, x + height * ratio, y + height)
        else:
            target_rect = pymupdf.Rect(x, y, x + img_rect.width, y + img_rect.height)

        pdf_page.insert_image(target_rect, stream=image_data)
        img_doc.close()
        self._truncate_and_save()

    def draw_shape(
        self,
        page: int,
        shape_type: ShapeType,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        color: Tuple[float, float, float] = (0, 0, 0),
        fill: Optional[Tuple[float, float, float]] = None,
        width: float = 1.0,
    ):
        if page < 1 or page > len(self.doc):
            raise ValueError(f"Invalid page: {page}")
        pdf_page = self.doc[page - 1]
        shape = pdf_page.new_shape()
        rect = pymupdf.Rect(x0, y0, x1, y1)

        if shape_type == ShapeType.RECT:
            shape.draw_rect(rect)
        elif shape_type == ShapeType.CIRCLE:
            shape.draw_circle(((x0 + x1) / 2, (y0 + y1) / 2), min(abs(x1 - x0), abs(y1 - y0)) / 2)
        elif shape_type == ShapeType.LINE:
            shape.draw_line((x0, y0), (x1, y1))

        shape.finish(color=color, fill=fill, width=width)
        shape.commit()
        self._truncate_and_save()

    def add_annotation(
        self,
        page: int,
        annot_type: AnnotationType,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        text: str = "",
        color: Tuple[float, float, float] = (1, 1, 0),
    ):
        if page < 1 or page > len(self.doc):
            raise ValueError(f"Invalid page: {page}")
        pdf_page = self.doc[page - 1]
        rect = pymupdf.Rect(x0, y0, x1, y1)

        type_map = {
            AnnotationType.HIGHLIGHT: pymupdf.PDF_ANNOT_HIGHLIGHT,
            AnnotationType.UNDERLINE: pymupdf.PDF_ANNOT_UNDERLINE,
            AnnotationType.STRIKEOUT: pymupdf.PDF_ANNOT_STRIKE_OUT,
            AnnotationType.FREETEXT: pymupdf.PDF_ANNOT_FREE_TEXT,
            AnnotationType.STICKY: pymupdf.PDF_ANNOT_TEXT,
        }

        annot = pdf_page.add_highlight_annot(rect) if annot_type == AnnotationType.HIGHLIGHT else \
                pdf_page.add_underline_annot(rect) if annot_type == AnnotationType.UNDERLINE else \
                pdf_page.add_strikeout_annot(rect) if annot_type == AnnotationType.STRIKEOUT else \
                pdf_page.add_freetext_annot(rect, text, fontsize=12, text_color=color) if annot_type == AnnotationType.FREETEXT else \
                pdf_page.add_text_annot((x0, y0), text)

        if annot_type in (AnnotationType.HIGHLIGHT, AnnotationType.UNDERLINE, AnnotationType.STRIKEOUT):
            annot.set_colors(stroke=color)
            annot.update()

        self._truncate_and_save()

    def move_element(
        self,
        page: int,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        dx: float,
        dy: float,
    ):
        if page < 1 or page > len(self.doc):
            raise ValueError(f"Invalid page: {page}")
        pdf_page = self.doc[page - 1]
        src = pymupdf.Rect(x0, y0, x1, y1)
        dst = pymupdf.Rect(x0 + dx, y0 + dy, x1 + dx, y1 + dy)
        clip = src
        pix = pdf_page.get_pixmap(clip=src, dpi=150)
        shape = pdf_page.new_shape()
        shape.draw_rect(src)
        shape.finish(fill=(1, 1, 1), color=(1, 1, 1))
        shape.commit(overlay=True)
        pdf_page.insert_image(dst, pixmap=pix)
        self._truncate_and_save()

    def resize_element(
        self,
        page: int,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        width: float,
        height: float,
    ):
        if page < 1 or page > len(self.doc):
            raise ValueError(f"Invalid page: {page}")
        pdf_page = self.doc[page - 1]
        src = pymupdf.Rect(x0, y0, x1, y1)
        dst = pymupdf.Rect(x0, y0, x0 + width, y0 + height)
        pix = pdf_page.get_pixmap(clip=src, dpi=150)
        shape = pdf_page.new_shape()
        shape.draw_rect(src)
        shape.finish(fill=(1, 1, 1), color=(1, 1, 1))
        shape.commit(overlay=True)
        pdf_page.insert_image(dst, pixmap=pix)
        self._truncate_and_save()

    def save(self, output_path: Union[str, Path]):
        self.doc.save(str(output_path))

    def get_bytes(self) -> bytes:
        buf = io.BytesIO()
        self.doc.save(buf)
        return buf.getvalue()

    def close(self):
        try:
            if self.doc and not self.doc.is_closed:
                self.doc.close()
        except Exception:
            pass
