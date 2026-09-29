import io
from pathlib import Path
import pytest
import pymupdf
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from packages.ocr_engine import OcrEngine
from packages.signature_engine import SignatureEngine


@pytest.fixture
def ocr_engine():
    return OcrEngine()


@pytest.fixture
def signature_engine():
    return SignatureEngine()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "Test Page", fontsize=24)
    
    output = io.BytesIO()
    doc.save(output)
    doc.close()
    return output.getvalue()


class TestOcrEngine:
    def test_get_available_providers(self, ocr_engine):
        providers = ocr_engine.get_available_providers()
        assert isinstance(providers, list)

    def test_provider_fallback(self, ocr_engine):
        try:
            _ = ocr_engine.provider
        except RuntimeError:
            pass


class TestSignatureEngine:
    def test_create_typed_signature(self, signature_engine):
        sig_data = signature_engine.create_typed_signature("John Doe")
        
        assert sig_data is not None
        assert len(sig_data) > 0
        
        img = Image.open(io.BytesIO(sig_data))
        assert img.format == "PNG"

    def test_add_signature(self, signature_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "signed.pdf"
        sig_file = tmp_path / "sig.png"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        sig_data = signature_engine.create_typed_signature("Test")
        sig_file.write_bytes(sig_data)
        
        signature_engine.add_signature(
            str(input_file),
            str(output_file),
            sig_data,
            page=1,
            x=100,
            y=100,
        )
        
        assert output_file.exists()
        
        doc = pymupdf.open(str(output_file))
        assert len(doc) == 1
        doc.close()

    def test_add_text_field(self, signature_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "with_field.pdf"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        signature_engine.add_text_field(
            str(input_file),
            str(output_file),
            field_id="text_field_1",
            page=1,
            x=100,
            y=200,
            width=200,
            height=30,
        )
        
        assert output_file.exists()

    def test_add_checkbox(self, signature_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "with_checkbox.pdf"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        signature_engine.add_checkbox(
            str(input_file),
            str(output_file),
            field_id="checkbox_1",
            page=1,
            x=100,
            y=250,
            size=20,
            label="Agree",
        )
        
        assert output_file.exists()

    def test_create_signature_request(self, signature_engine):
        signers = [
            {"name": "John Doe", "email": "john@example.com"},
            {"name": "Jane Smith", "email": "jane@example.com"},
        ]
        
        request = signature_engine.create_signature_request("test.pdf", signers)
        
        assert "id" in request
        assert request["status"] == "pending"
        assert len(request["signers"]) == 2
