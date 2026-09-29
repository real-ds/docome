"""Page rasterization and thumbnail generation.

The editor and web UI both need small page previews. Rendering each page
separately at a given DPI keeps memory bounded and avoids handing callers a
full-resolution pixmap they have to scale down themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pymupdf

MIN_DPI = 18
MAX_DPI = 600

JPEG_QUALITY = 82

IMAGE_MEDIA_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}


@dataclass
class PageImage:
    """A rendered page."""

    page: int
    width: int
    height: int
    dpi: int
    media_type: str
    data: bytes

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "width": self.width,
            "height": self.height,
            "dpi": self.dpi,
            "media_type": self.media_type,
            "bytes": len(self.data),
        }


def _open(source: Union[str, Path, bytes]) -> pymupdf.Document:
    if isinstance(source, bytes):
        return pymupdf.open(stream=source, filetype="pdf")
    return pymupdf.open(str(source))


def _resolve_dpi(dpi: Optional[float]) -> float:
    if dpi is None:
        return MIN_DPI
    value = float(dpi)
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError("dpi must be a finite number")
    if value < MIN_DPI:
        raise ValueError(f"dpi must be at least {MIN_DPI}")
    if value > MAX_DPI:
        raise ValueError(f"dpi must be at most {MAX_DPI}")
    # PyMuPDF only accepts whole numbers here and silently truncates floats.
    return int(round(value))


def _validate_format(image_format: str) -> str:
    key = (image_format or "png").lower()
    if key not in IMAGE_MEDIA_TYPES:
        allowed = ", ".join(sorted(IMAGE_MEDIA_TYPES))
        raise ValueError(f"format must be one of: {allowed}")
    return key


def _encode(pixmap: pymupdf.Pixmap, image_format: str) -> bytes:
    if image_format == "png":
        return pixmap.tobytes("png")
    # JPEG has no alpha channel, so flatten onto white first.
    if pixmap.alpha:
        pixmap = pymupdf.Pixmap(pixmap, 0)
    return pixmap.tobytes("jpg", jpg_quality=JPEG_QUALITY)


def render_page(
    source: Union[str, Path, bytes],
    page: int = 1,
    dpi: Optional[float] = None,
    image_format: str = "png",
) -> PageImage:
    """Render one page to an encoded image."""
    resolved_dpi = _resolve_dpi(dpi)
    key = _validate_format(image_format)

    document = _open(source)
    try:
        if page < 1 or page > document.page_count:
            raise ValueError(f"Invalid page: {page} (document has {document.page_count})")
        pixmap = document[page - 1].get_pixmap(dpi=resolved_dpi)
        try:
            data = _encode(pixmap, key)
            return PageImage(
                page=page,
                width=pixmap.width,
                height=pixmap.height,
                dpi=int(round(resolved_dpi)),
                media_type=IMAGE_MEDIA_TYPES[key],
                data=data,
            )
        finally:
            pixmap = None
    finally:
        document.close()


def render_pages(
    source: Union[str, Path, bytes],
    pages: Optional[List[int]] = None,
    dpi: Optional[float] = None,
    image_format: str = "png",
) -> List[PageImage]:
    """Render several pages, defaulting to every page."""
    resolved_dpi = _resolve_dpi(dpi)
    key = _validate_format(image_format)

    document = _open(source)
    try:
        targets = pages or list(range(1, document.page_count + 1))
        results: List[PageImage] = []
        for number in targets:
            if number < 1 or number > document.page_count:
                raise ValueError(
                    f"Invalid page: {number} (document has {document.page_count})"
                )
            pixmap = document[number - 1].get_pixmap(dpi=resolved_dpi)
            data = _encode(pixmap, key)
            results.append(
                PageImage(
                    page=number,
                    width=pixmap.width,
                    height=pixmap.height,
                    dpi=int(round(resolved_dpi)),
                    media_type=IMAGE_MEDIA_TYPES[key],
                    data=data,
                )
            )
        return results
    finally:
        document.close()


def thumbnail_size(
    source: Union[str, Path, bytes],
    max_dimension: int = 240,
) -> List[Tuple[int, Tuple[int, int]]]:
    """Report the pixel size each page would have at a fitted thumbnail size.

    Pages keep their aspect ratio and are never scaled above their natural
    size, so a small page is not blown up into a blurry image.
    """
    if max_dimension < 1:
        raise ValueError("max_dimension must be positive")

    document = _open(source)
    try:
        sizes: List[Tuple[int, Tuple[int, int]]] = []
        for index in range(document.page_count):
            rect = document[index].rect
            if rect.width <= 0 or rect.height <= 0:
                sizes.append((index + 1, (0, 0)))
                continue
            scale = min(1.0, max_dimension / max(rect.width, rect.height))
            sizes.append((index + 1, (int(rect.width * scale), int(rect.height * scale))))
        return sizes
    finally:
        document.close()
