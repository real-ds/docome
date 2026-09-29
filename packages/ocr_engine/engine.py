import io
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

import pymupdf


class OcrProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def process_image(self, image_bytes: bytes, lang: str = "eng") -> str:
        pass

    @abstractmethod
    def process_pdf_page(self, page, lang: str = "eng") -> str:
        pass


class TesseractProvider(OcrProvider):
    def __init__(self):
        self._available = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._available = True
        except Exception:
            self._available = False
        
        return self._available

    def process_image(self, image_bytes: bytes, lang: str = "eng") -> str:
        import pytesseract
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img, lang=lang)

    def process_pdf_page(self, page, lang: str = "eng") -> str:
        import pytesseract
        from PIL import Image

        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        return pytesseract.image_to_string(img, lang=lang)


class EasyOcrProvider(OcrProvider):
    def __init__(self):
        self._available = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        
        try:
            import easyocr
            self._available = True
        except ImportError:
            self._available = False
        
        return self._available

    def process_image(self, image_bytes: bytes, lang: str = "eng") -> str:
        import easyocr

        lang_code = "en" if lang == "eng" else lang
        reader = easyocr.Reader([lang_code], gpu=False)
        results = reader.readtext(image_bytes)
        
        return "\n".join([text for _, text, _ in results])

    def process_pdf_page(self, page, lang: str = "eng") -> str:
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        
        return self.process_image(img_bytes, lang)


class OcrEngine:
    def __init__(self, provider: Optional[OcrProvider] = None):
        self._provider = provider

    @property
    def provider(self) -> OcrProvider:
        if self._provider is not None:
            return self._provider
        
        for provider_class in [TesseractProvider, EasyOcrProvider]:
            provider = provider_class()
            if provider.is_available():
                self._provider = provider
                return provider
        
        raise RuntimeError("No OCR provider available. Install pytesseract or easyocr.")

    def pdf_to_searchable(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        lang: str = "eng",
    ) -> None:
        if isinstance(input_path, bytes):
            pdf_doc = pymupdf.open(stream=input_path, filetype="pdf")
        else:
            pdf_doc = pymupdf.open(input_path)

        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            
            text = page.get_text()
            if not text.strip():
                try:
                    ocr_text = self.provider.process_pdf_page(page, lang)
                    
                    page.insert_text((50, 50), ocr_text, fontsize=0)
                except Exception:
                    pass

        pdf_doc.save(output_path)
        pdf_doc.close()

    def extract_text_from_image(
        self,
        image_path: Union[str, Path, bytes],
        lang: str = "eng",
    ) -> str:
        if isinstance(image_path, bytes):
            return self.provider.process_image(image_path, lang)
        else:
            with open(image_path, "rb") as f:
                return self.provider.process_image(f.read(), lang)

    def get_available_providers(self) -> List[str]:
        providers = []
        
        if TesseractProvider().is_available():
            providers.append("tesseract")
        if EasyOcrProvider().is_available():
            providers.append("easyocr")
        
        return providers
