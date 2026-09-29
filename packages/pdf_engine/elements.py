"""Element discovery and hit testing for PDF pages.

Editing operations currently address content by raw coordinates, which means
callers have to know the exact bounding box of what they want to change and
have no way to discover what is on the page. This module enumerates the
addressable elements of a page and resolves a point or rectangle to the
elements underneath it.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Sequence, Tuple

import pymupdf


class ElementKind(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DRAWING = "drawing"
    ANNOTATION = "annotation"


class Element:
    """One addressable item on a page."""

    __slots__ = ("id", "page", "kind", "rect", "text", "font", "size", "color", "rotation", "uri")

    def __init__(
        self,
        id: str,
        page: int,
        kind: ElementKind,
        rect: pymupdf.Rect,
        text: Optional[str] = None,
        font: Optional[str] = None,
        size: Optional[float] = None,
        color: Optional[int] = None,
        rotation: int = 0,
        uri: Optional[str] = None,
    ):
        self.id = id
        self.page = page
        self.kind = kind
        self.rect = pymupdf.Rect(rect)
        self.text = text
        self.font = font
        self.size = size
        self.color = color
        self.rotation = rotation
        self.uri = uri

    @property
    def width(self) -> float:
        return self.rect.width

    @property
    def height(self) -> float:
        return self.rect.height

    def contains(self, x: float, y: float) -> bool:
        return self.rect.contains((x, y))

    def overlaps(self, rect: pymupdf.Rect) -> bool:
        return bool(self.rect.intersects(rect))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "page": self.page,
            "kind": self.kind.value,
            "x0": round(self.rect.x0, 2),
            "y0": round(self.rect.y0, 2),
            "x1": round(self.rect.x1, 2),
            "y1": round(self.rect.y1, 2),
            "text": self.text,
            "font": self.font,
            "size": round(self.size, 2) if self.size is not None else None,
            "color": self.color,
            "rotation": self.rotation,
            "uri": self.uri,
        }

    def __repr__(self) -> str:
        return f"Element({self.id}, {self.kind.value}, page={self.page}, rect={tuple(self.rect)})"


def _text_elements(page: pymupdf.Page, page_number: int) -> List[Element]:
    elements: List[Element] = []
    counter = 0
    data = page.get_text("dict")
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "")
                bbox = span.get("bbox")
                if not text.strip() or not bbox:
                    continue
                elements.append(
                    Element(
                        id=f"p{page_number}-t{counter}",
                        page=page_number,
                        kind=ElementKind.TEXT,
                        rect=pymupdf.Rect(bbox),
                        text=text,
                        font=span.get("font"),
                        size=span.get("size"),
                        color=span.get("color"),
                    )
                )
                counter += 1
    return elements


def _image_elements(page: pymupdf.Page, page_number: int) -> List[Element]:
    elements: List[Element] = []
    for index, info in enumerate(page.get_images(full=True)):
        xref = info[0]
        try:
            rects = page.get_image_rects(xref)
        except (ValueError, RuntimeError):
            rects = []
        for rect_index, rect in enumerate(rects):
            elements.append(
                Element(
                    id=f"p{page_number}-i{index}-{rect_index}",
                    page=page_number,
                    kind=ElementKind.IMAGE,
                    rect=rect,
                )
            )
    return elements


def _drawing_elements(page: pymupdf.Page, page_number: int) -> List[Element]:
    elements: List[Element] = []
    for index, drawing in enumerate(page.get_drawings()):
        rect = drawing.get("rect")
        if rect is None:
            continue
        rect = pymupdf.Rect(rect)
        if rect.is_empty or rect.is_infinite:
            continue
        elements.append(
            Element(
                id=f"p{page_number}-d{index}",
                page=page_number,
                kind=ElementKind.DRAWING,
                rect=rect,
            )
        )
    return elements


def _annotation_elements(page: pymupdf.Page, page_number: int) -> List[Element]:
    elements: List[Element] = []
    for annot in page.annots() or []:
        info = annot.info or {}
        elements.append(
            Element(
                id=f"p{page_number}-a{annot.xref}",
                page=page_number,
                kind=ElementKind.ANNOTATION,
                rect=pymupdf.Rect(annot.rect),
                text=info.get("content"),
                rotation=int(annot.rotation or 0),
                uri=info.get("uri"),
            )
        )
    return elements


_COLLECTORS = {
    ElementKind.TEXT: _text_elements,
    ElementKind.IMAGE: _image_elements,
    ElementKind.DRAWING: _drawing_elements,
    ElementKind.ANNOTATION: _annotation_elements,
}


def list_elements(
    page: pymupdf.Page,
    page_number: int,
    kinds: Optional[Sequence[ElementKind]] = None,
) -> List[Element]:
    """Return the elements of a page, optionally filtered by kind."""
    selected = list(kinds) if kinds else list(_COLLECTORS)
    found: List[Element] = []
    for kind in selected:
        collector = _COLLECTORS.get(kind)
        if collector is not None:
            found.extend(collector(page, page_number))
    return found


def find_at(
    page: pymupdf.Page,
    page_number: int,
    x: float,
    y: float,
    kinds: Optional[Sequence[ElementKind]] = None,
) -> List[Element]:
    """Return elements under a point, topmost first.

    Annotations sit above page content, and images and drawings are painted
    before text, so the order here is the reverse of the painting order.
    """
    point = pymupdf.Point(x, y)
    if not page.rect.contains(point):
        return []

    priority = {
        ElementKind.ANNOTATION: 0,
        ElementKind.TEXT: 1,
        ElementKind.IMAGE: 2,
        ElementKind.DRAWING: 3,
    }
    hits = [element for element in list_elements(page, page_number, kinds) if element.contains(x, y)]
    hits.sort(key=lambda element: priority.get(element.kind, 99))
    return hits


def find_in_rect(
    page: pymupdf.Page,
    page_number: int,
    rect: pymupdf.Rect,
    kinds: Optional[Sequence[ElementKind]] = None,
) -> List[Element]:
    """Return elements overlapping a rectangle."""
    area = pymupdf.Rect(rect)
    if area.is_empty or area.is_infinite:
        return []
    return [
        element
        for element in list_elements(page, page_number, kinds)
        if element.overlaps(area)
    ]


def element_by_id(
    page: pymupdf.Page,
    page_number: int,
    element_id: str,
) -> Optional[Element]:
    for element in list_elements(page, page_number):
        if element.id == element_id:
            return element
    return None
