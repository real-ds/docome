import io
from pathlib import Path
from typing import List, Optional, Union

import pymupdf
from PIL import Image


class ImageEngine:
    def __init__(self):
        pass

    def images_to_pdf(
        self,
        image_paths: List[Union[str, Path, bytes]],
        output_path: Union[str, Path],
    ) -> None:
        output_path = Path(output_path)
        doc = pymupdf.open()

        for img_path in image_paths:
            if isinstance(img_path, bytes):
                img = Image.open(io.BytesIO(img_path))
            else:
                img = Image.open(img_path)

            if img.mode == "RGBA":
                img = img.convert("RGB")

            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG", quality=95)
            img_bytes.seek(0)

            page = doc.new_page(width=img.width, height=img.height)
            page.insert_image(page.rect, stream=img_bytes.getvalue())

        doc.save(output_path)
        doc.close()

    def pdf_to_images(
        self,
        input_path: Union[str, Path, bytes],
        output_dir: Union[str, Path],
        dpi: int = 150,
        fmt: str = "PNG",
    ) -> List[Path]:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_files = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=dpi)

            output_file = output_dir / f"page_{page_num + 1:03d}.{fmt.lower()}"
            pix.save(output_file, output=fmt)
            output_files.append(output_file)

        doc.close()
        return output_files

    def pdf_page_to_image(
        self,
        input_path: Union[str, Path, bytes],
        page_number: int = 1,
        dpi: int = 150,
        fmt: str = "PNG",
    ) -> bytes:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        if page_number < 1 or page_number > len(doc):
            raise ValueError(f"Page {page_number} out of range (1-{len(doc)})")

        page = doc[page_number - 1]
        pix = page.get_pixmap(dpi=dpi)

        output = io.BytesIO()
        pix.save(output, output=fmt)

        doc.close()
        return output.getvalue()

    def get_image_info(
        self,
        input_path: Union[str, Path, bytes],
    ) -> dict:
        if isinstance(input_path, bytes):
            img = Image.open(io.BytesIO(input_path))
        else:
            img = Image.open(input_path)

        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
        }
