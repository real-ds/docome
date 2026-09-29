import io
from pathlib import Path
from typing import Generator
import pytest
import pymupdf

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from packages.pdf_engine import PdfEngine, CompressLevel, Metadata, PageRange, Rotation
from packages.image_engine import ImageEngine


@pytest.fixture
def pdf_engine():
    return PdfEngine()


@pytest.fixture
def image_engine():
    return ImageEngine()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    import pymupdf
    
    doc = pymupdf.open()
    for i in range(3):
        page = doc.new_page(width=595, height=842)
        text_point = pymupdf.Point(72, 72)
        page.insert_text(text_point, f"Page {i + 1}", fontsize=24)
    
    output = io.BytesIO()
    doc.save(output)
    doc.close()
    
    return output.getvalue()


@pytest.fixture
def sample_image_bytes() -> bytes:
    from PIL import Image
    
    img = Image.new("RGB", (200, 100), color="red")
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    
    return output.getvalue()


class TestMerge:
    def test_merge_multiple_pdfs(self, pdf_engine, sample_pdf_bytes, tmp_path):
        file1 = tmp_path / "file1.pdf"
        file2 = tmp_path / "file2.pdf"
        output = tmp_path / "merged.pdf"
        
        with open(file1, "wb") as f:
            f.write(sample_pdf_bytes)
        with open(file2, "wb") as f:
            f.write(sample_pdf_bytes)
        
        pdf_engine.merge([str(file1), str(file2)], str(output))
        
        assert output.exists()
        
        doc = pymupdf.open(str(output))
        assert len(doc) == 6
        doc.close()


class TestSplit:
    def test_split_by_single_page(self, pdf_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_dir = tmp_path / "output"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        result = pdf_engine.split(str(input_file), str(output_dir), pages_per_split=1)
        
        assert len(result) == 3
        for f in result:
            doc = pymupdf.open(str(f))
            assert len(doc) == 1
            doc.close()


class TestExtract:
    def test_extract_pages(self, pdf_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output = tmp_path / "extracted.pdf"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        pdf_engine.extract(str(input_file), str(output), pages=[0, 2])
        
        doc = pymupdf.open(str(output))
        assert len(doc) == 2
        doc.close()


class TestRemove:
    def test_remove_pages(self, pdf_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output = tmp_path / "output.pdf"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        pdf_engine.remove(str(input_file), str(output), pages=[1])
        
        doc = pymupdf.open(str(output))
        assert len(doc) == 2
        doc.close()


class TestRotate:
    def test_rotate_all_pages(self, pdf_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output = tmp_path / "output.pdf"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        pdf_engine.rotate(str(input_file), str(output), Rotation.ROTATE_90)
        
        doc = pymupdf.open(str(output))
        assert doc[0].rotation == 90
        doc.close()


class TestCompress:
    def test_compress_pdf(self, pdf_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output = tmp_path / "compressed.pdf"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        original_size = input_file.stat().st_size
        
        pdf_engine.compress(str(input_file), str(output), CompressLevel.RECOMMENDED)
        
        compressed_size = output.stat().st_size
        assert compressed_size < original_size


class TestMetadata:
    def test_get_metadata(self, pdf_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        meta = pdf_engine.get_metadata(str(input_file))
        
        assert meta is not None

    def test_set_metadata(self, pdf_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output = tmp_path / "output.pdf"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        new_meta = Metadata(title="Test Title", author="Test Author")
        pdf_engine.set_metadata(str(input_file), str(output), new_meta)
        
        result = pdf_engine.get_metadata(str(output))
        assert result.title == "Test Title"
        assert result.author == "Test Author"


class TestProtect:
    def test_protect_pdf(self, pdf_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output = tmp_path / "protected.pdf"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        pdf_engine.protect(str(input_file), str(output), "testpass123")
        
        doc = pymupdf.open(str(output))
        assert doc.is_encrypted
        doc.close()


class TestPageCount:
    def test_get_page_count(self, pdf_engine, sample_pdf_bytes):
        count = pdf_engine.get_page_count(sample_pdf_bytes)
        assert count == 3


class TestImagesToPdf:
    def test_images_to_pdf(self, image_engine, sample_image_bytes, tmp_path):
        output = tmp_path / "output.pdf"
        
        image_engine.images_to_pdf([sample_image_bytes], str(output))
        
        assert output.exists()
        
        import pymupdf
        doc = pymupdf.open(str(output))
        assert len(doc) == 1
        doc.close()


class TestPdfToImages:
    def test_pdf_to_images(self, pdf_engine, image_engine, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_dir = tmp_path / "images"
        
        with open(input_file, "wb") as f:
            f.write(sample_pdf_bytes)
        
        result = image_engine.pdf_to_images(str(input_file), str(output_dir))
        
        assert len(result) == 3
        for f in result:
            assert f.exists()
