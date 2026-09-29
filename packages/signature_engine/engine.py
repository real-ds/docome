import io
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

import pymupdf
from PIL import Image, ImageDraw, ImageFont


class SignatureEngine:
    def __init__(self):
        pass

    def create_typed_signature(
        self,
        name: str,
        font_size: int = 40,
    ) -> bytes:
        img = Image.new("RGBA", (400, 100), color=(255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        img = img.crop((0, 0, text_width + 20, text_height + 20))
        draw = ImageDraw.Draw(img)
        
        draw.text((10, 10), name, fill=(0, 0, 0, 255), font=font)
        
        output = io.BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()

    def add_signature(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        signature_data: bytes,
        page: int = 1,
        x: float = 100,
        y: float = 100,
        width: Optional[float] = None,
        height: Optional[float] = None,
    ) -> None:
        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        if page < 1 or page > len(pdf_doc):
            raise ValueError(f"Invalid page number: {page}")

        pdf_page = pdf_doc[page - 1]

        rect = pymupdf.Rect(x, y, x + 200, y + 50)
        if width and height:
            rect = pymupdf.Rect(x, y, x + width, y + height)

        pdf_page.insert_image(rect, stream=signature_data)

        pdf_doc.save(output_path)
        pdf_doc.close()

    def add_signature_field(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        field_id: str,
        page: int = 1,
        x: float = 100,
        y: float = 100,
        width: float = 200,
        height: float = 50,
    ) -> None:
        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        if page < 1 or page > len(pdf_doc):
            raise ValueError(f"Invalid page number: {page}")

        pdf_page = pdf_doc[page - 1]

        rect = pymupdf.Rect(x, y, x + width, y + height)
        pdf_page.draw_rect(rect, color=(0.5, 0.5, 0.5), fill=(0.95, 0.95, 0.95), border=1)
        pdf_page.insert_text((x + 5, y + height / 2), f"[Signature: {field_id}]", fontsize=10)

        pdf_doc.save(output_path)
        pdf_doc.close()

    def fill_signature_field(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        field_id: str,
        signature_data: bytes,
    ) -> None:
        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            
            for annot in page.annots():
                if annot.field_name == field_id:
                    rect = annot.rect
                    page.insert_image(rect, stream=signature_data)
                    break

        pdf_doc.save(output_path)
        pdf_doc.close()

    def create_signature_request(
        self,
        document_path: Union[str, Path],
        signers: List[dict],
    ) -> dict:
        request_id = str(uuid.uuid4())
        
        return {
            "id": request_id,
            "document_path": str(document_path),
            "signers": signers,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }

    def add_text_field(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        field_id: str,
        page: int = 1,
        x: float = 100,
        y: float = 100,
        width: float = 200,
        height: float = 30,
        default_value: Optional[str] = None,
    ) -> None:
        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        if page < 1 or page > len(pdf_doc):
            raise ValueError(f"Invalid page number: {page}")

        pdf_page = pdf_doc[page - 1]
        value = default_value or field_id
        
        rect = pymupdf.Rect(x, y, x + width, y + height)
        shape = pdf_page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=(0.7, 0.7, 0.7), fill=None, stroke_opacity=1)
        shape.commit()
        
        pdf_page.insert_text((x + 5, y + height - 5), f"[{value}]", fontsize=8)

        pdf_doc.save(output_path)
        pdf_doc.close()

    def add_date_field(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        field_id: str,
        page: int = 1,
        x: float = 100,
        y: float = 100,
        width: float = 150,
        height: float = 30,
    ) -> None:
        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        if page < 1 or page > len(pdf_doc):
            raise ValueError(f"Invalid page number: {page}")

        pdf_page = pdf_doc[page - 1]

        rect = pymupdf.Rect(x, y, x + width, y + height)
        shape = pdf_page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=(0.7, 0.7, 0.7), fill=None, stroke_opacity=1)
        shape.commit()
        
        pdf_page.insert_text((x + 5, y + height - 5), "[Date]", fontsize=8)

        pdf_doc.save(output_path)
        pdf_doc.close()

    def add_checkbox(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        field_id: str,
        page: int = 1,
        x: float = 100,
        y: float = 100,
        size: float = 20,
        label: Optional[str] = None,
    ) -> None:
        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        if page < 1 or page > len(pdf_doc):
            raise ValueError(f"Invalid page number: {page}")

        pdf_page = pdf_doc[page - 1]

        rect = pymupdf.Rect(x, y, x + size, y + size)
        shape = pdf_page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=(0, 0, 0), fill=None, stroke_opacity=1)
        shape.commit()
        
        if label:
            pdf_page.insert_text((x + size + 5, y + size - 3), label, fontsize=10)

        pdf_doc.save(output_path)
        pdf_doc.close()
