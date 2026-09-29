import io
from pathlib import Path
from typing import List, Optional, Union

import pymupdf
from pikepdf import Pdf, new

from .models import CompressLevel, Metadata, PageRange, Rotation


class PdfEngine:
    def __init__(self):
        pass

    def merge(
        self,
        input_paths: List[Union[str, Path, bytes]],
        output_path: Union[str, Path],
    ) -> None:
        output_path = Path(output_path)
        result = new()

        for input_path in input_paths:
            if isinstance(input_path, bytes):
                src = Pdf.open(io.BytesIO(input_path))
            else:
                src = Pdf.open(input_path)

            result.pages.extend(src.pages)
            src.close()

        result.save(output_path)

    def split(
        self,
        input_path: Union[str, Path, bytes],
        output_dir: Union[str, Path],
        pages_per_split: int = 1,
    ) -> List[Path]:
        input_path = Path(input_path) if not isinstance(input_path, (str, Path)) or Path(input_path).exists() else None
        
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_files = []
        base_name = "split"

        for i in range(0, len(doc), pages_per_split):
            new_doc = pymupdf.open()
            for page_num in range(i, min(i + pages_per_split, len(doc))):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            output_file = output_dir / f"{base_name}_{i // pages_per_split + 1:03d}.pdf"
            new_doc.save(output_file)
            output_files.append(output_file)
            new_doc.close()

        doc.close()
        return output_files

    def extract(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        pages: Optional[List[int]] = None,
        page_range: Optional[PageRange] = None,
    ) -> None:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        new_doc = pymupdf.open()

        if page_range:
            pages = page_range.to_pages(len(doc))
        elif pages is None:
            pages = list(range(len(doc)))

        for page_num in pages:
            if 0 <= page_num < len(doc):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        new_doc.save(output_path)
        new_doc.close()
        doc.close()

    def remove(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        pages: Optional[List[int]] = None,
        page_range: Optional[PageRange] = None,
    ) -> None:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        new_doc = pymupdf.open()

        if page_range:
            pages_to_remove = set(page_range.to_pages(len(doc)))
        elif pages:
            pages_to_remove = set(pages)
        else:
            pages_to_remove = set()

        for i in range(len(doc)):
            if i not in pages_to_remove:
                new_doc.insert_pdf(doc, from_page=i, to_page=i)

        new_doc.save(output_path)
        new_doc.close()
        doc.close()

    def reorder(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        new_order: List[int],
    ) -> None:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        new_doc = pymupdf.open()

        for page_num in new_order:
            if 0 <= page_num < len(doc):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        new_doc.save(output_path)
        new_doc.close()
        doc.close()

    def rotate(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        rotation: Rotation,
        pages: Optional[List[int]] = None,
        page_range: Optional[PageRange] = None,
    ) -> None:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        rotation_degrees = int(rotation.value)

        if page_range:
            pages = page_range.to_pages(len(doc))

        for i in range(len(doc)):
            if pages is None or i in pages:
                page = doc[i]
                page.set_rotation(page.rotation + rotation_degrees)

        doc.save(output_path)
        doc.close()

    def compress(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        level: CompressLevel = CompressLevel.RECOMMENDED,
    ) -> None:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        compression_settings = {
            CompressLevel.EXTREME: {"images": 40, "fonts": 40},
            CompressLevel.HIGH: {"images": 60, "fonts": 60},
            CompressLevel.RECOMMENDED: {"images": 80, "fonts": 80},
            CompressLevel.LOW: {"images": 95, "fonts": 95},
        }

        settings = compression_settings.get(level, compression_settings[CompressLevel.RECOMMENDED])

        for page_num in range(len(doc)):
            page = doc[page_num]
            for img_index in range(len(page.get_images())):
                xref = page.get_images()[img_index][0]
                img = doc.extract_image(xref)
                if img:
                    doc.reconstruct_image(xref, compression=settings["images"])

        doc.save(output_path, garbage=4, deflate=True, deflate_images=True)
        doc.close()

    def get_metadata(self, input_path: Union[str, Path, bytes]) -> Metadata:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        meta = doc.metadata

        metadata = Metadata(
            title=meta.get("title"),
            author=meta.get("author"),
            subject=meta.get("subject"),
            creator=meta.get("creator"),
            producer=meta.get("producer"),
            keywords=meta.get("keywords"),
            creation_date=meta.get("creationDate"),
            mod_date=meta.get("modDate"),
        )

        doc.close()
        return metadata

    def set_metadata(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        metadata: Metadata,
    ) -> None:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        meta = {}
        if metadata.title is not None:
            meta["title"] = metadata.title
        if metadata.author is not None:
            meta["author"] = metadata.author
        if metadata.subject is not None:
            meta["subject"] = metadata.subject
        if metadata.creator is not None:
            meta["creator"] = metadata.creator
        if metadata.producer is not None:
            meta["producer"] = metadata.producer
        if metadata.keywords is not None:
            meta["keywords"] = metadata.keywords

        doc.set_metadata(meta)
        doc.save(output_path)
        doc.close()

    def protect(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        password: str,
        owner_password: Optional[str] = None,
    ) -> None:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        owner_pw = owner_password or password

        doc.save(
            str(output_path),
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            user_pw=password,
            owner_pw=owner_pw,
        )
        doc.close()

    def unlock(
        self,
        input_path: Union[str, Path, bytes],
        password: str,
    ) -> bytes:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)

        if doc.is_encrypted:
            if not doc.authenticate(password):
                raise ValueError("Invalid password")

        output = io.BytesIO()
        doc.save(output)
        doc.close()
        return output.getvalue()

    def get_page_count(self, input_path: Union[str, Path, bytes]) -> int:
        if isinstance(input_path, bytes):
            doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            doc = pymupdf.open(input_path)
        
        count = len(doc)
        doc.close()
        return count
