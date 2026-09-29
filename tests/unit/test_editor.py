import io
from pathlib import Path
import pytest
import pymupdf

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from packages.pdf_engine import EditorSession, ShapeType, AnnotationType


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "Test Page", fontsize=24)
    page.insert_text((72, 120), "Existing content", fontsize=12)
    output = io.BytesIO()
    doc.save(output)
    doc.close()
    return output.getvalue()


class TestEditorSession:
    def test_add_text(self, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "output.pdf"
        input_file.write_bytes(sample_pdf_bytes)

        session = EditorSession(str(input_file))
        session.add_text(1, 100, 100, "New text", fontsize=14, color=(1, 0, 0))
        session.save(str(output_file))
        session.close()

        assert output_file.exists()
        doc = pymupdf.open(str(output_file))
        assert len(doc) == 1
        text = doc[0].get_text()
        assert "New text" in text
        doc.close()

    def test_add_image(self, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "output.pdf"
        input_file.write_bytes(sample_pdf_bytes)

        # Create a small test image
        import pymupdf
        img_doc = pymupdf.open()
        img_page = img_doc.new_page(width=100, height=100)
        img_page.draw_rect(pymupdf.Rect(0, 0, 100, 100), color=(1, 0, 0), fill=(1, 0, 0))
        pix = img_page.get_pixmap()
        img_data = pix.tobytes("png")
        img_doc.close()

        session = EditorSession(str(input_file))
        session.add_image(1, img_data, 100, 100, width=50, height=50)
        session.save(str(output_file))
        session.close()

        doc = pymupdf.open(str(output_file))
        assert len(doc) == 1
        doc.close()

    def test_draw_shape_rect(self, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "output.pdf"
        input_file.write_bytes(sample_pdf_bytes)

        session = EditorSession(str(input_file))
        session.draw_shape(1, ShapeType.RECT, 50, 50, 150, 150, color=(0, 0, 1), fill=(0.5, 0.5, 1), width=2.0)
        session.save(str(output_file))
        session.close()

        doc = pymupdf.open(str(output_file))
        assert len(doc) == 1
        doc.close()

    def test_draw_shape_circle(self, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "output.pdf"
        input_file.write_bytes(sample_pdf_bytes)

        session = EditorSession(str(input_file))
        session.draw_shape(1, ShapeType.CIRCLE, 100, 100, 200, 200, color=(0, 1, 0), width=1.5)
        session.save(str(output_file))
        session.close()

        doc = pymupdf.open(str(output_file))
        assert len(doc) == 1
        doc.close()

    def test_draw_shape_line(self, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "output.pdf"
        input_file.write_bytes(sample_pdf_bytes)

        session = EditorSession(str(input_file))
        session.draw_shape(1, ShapeType.LINE, 0, 0, 300, 300, color=(1, 1, 0), width=3.0)
        session.save(str(output_file))
        session.close()

        doc = pymupdf.open(str(output_file))
        assert len(doc) == 1
        doc.close()

    def test_add_highlight_annotation(self, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "output.pdf"
        input_file.write_bytes(sample_pdf_bytes)

        session = EditorSession(str(input_file))
        session.add_annotation(1, AnnotationType.HIGHLIGHT, 72, 72, 200, 120, color=(1, 1, 0))
        session.save(str(output_file))
        session.close()

        doc = pymupdf.open(str(output_file))
        assert len(doc) == 1
        annots = list(doc[0].annots())
        assert len(annots) >= 1
        doc.close()

    def test_add_freetext_annotation(self, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "output.pdf"
        input_file.write_bytes(sample_pdf_bytes)

        session = EditorSession(str(input_file))
        session.add_annotation(1, AnnotationType.FREETEXT, 100, 100, 300, 150, text="Comment", color=(0, 0, 1))
        session.save(str(output_file))
        session.close()

        doc = pymupdf.open(str(output_file))
        assert len(doc) == 1
        annots = list(doc[0].annots())
        assert len(annots) >= 1
        doc.close()

    def test_undo_redo(self, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "output.pdf"
        input_file.write_bytes(sample_pdf_bytes)

        session = EditorSession(str(input_file))
        session.add_text(1, 100, 100, "First text")
        session.add_text(1, 100, 120, "Second text")
        assert session.undo() is True  # undoes "Second text"
        assert session.redo() is True  # redoes "Second text"
        session.save(str(output_file))
        session.close()

        doc = pymupdf.open(str(output_file))
        text = doc[0].get_text()
        assert "First text" in text
        assert "Second text" in text
        doc.close()

    def test_undo_on_empty(self, sample_pdf_bytes):
        session = EditorSession(sample_pdf_bytes)
        assert session.undo() is False
        session.close()

    def test_move_element(self, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "output.pdf"
        input_file.write_bytes(sample_pdf_bytes)

        session = EditorSession(str(input_file))
        session.move_element(1, 72, 72, 200, 120, dx=50, dy=50)
        session.save(str(output_file))
        session.close()

        doc = pymupdf.open(str(output_file))
        assert len(doc) == 1
        doc.close()

    def test_resize_element(self, sample_pdf_bytes, tmp_path):
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "output.pdf"
        input_file.write_bytes(sample_pdf_bytes)

        session = EditorSession(str(input_file))
        session.resize_element(1, 72, 72, 200, 120, width=150, height=80)
        session.save(str(output_file))
        session.close()

        doc = pymupdf.open(str(output_file))
        assert len(doc) == 1
        doc.close()

    def test_session_close(self, sample_pdf_bytes):
        session = EditorSession(sample_pdf_bytes)
        session.close()
        # Should not raise on double close
        session.close()


class TestEditorUndoRedoStack:
    def test_undo_redo_sequence(self, sample_pdf_bytes, tmp_path):
        session = EditorSession(sample_pdf_bytes)
        
        # Add multiple operations
        session.add_text(1, 50, 50, "Text 1")
        session.add_text(1, 50, 70, "Text 2")
        session.draw_shape(1, ShapeType.RECT, 10, 10, 100, 100)
        
        # Undo twice
        assert session.undo() is True  # undo draw_shape
        assert session.undo() is True  # undo "Text 2"
        
        # Redo once
        assert session.redo() is True  # redo "Text 2"
        
        session.close()

    def test_redo_stack_cleared_on_new_op(self, sample_pdf_bytes):
        session = EditorSession(sample_pdf_bytes)
        session.add_text(1, 50, 50, "Text 1")
        session.undo()  # undo it
        session.add_text(1, 50, 70, "Text 2")  # new operation should clear redo
        assert session.redo() is False  # nothing to redo
        session.close()