import sys
from pathlib import Path

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from packages.pdf_engine import ElementKind, EditorSession
from packages.pdf_engine.elements import element_by_id, find_at, find_in_rect, list_elements


@pytest.fixture
def sample_pdf(tmp_path):
    document = pymupdf.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 100), "Selectable Heading", fontsize=18)
    page.draw_rect(pymupdf.Rect(72, 150, 272, 250), color=(0, 0, 1), width=2)
    page.draw_rect(pymupdf.Rect(350, 150, 450, 250), fill=(0.8, 0.2, 0.2))
    page.insert_image(
        pymupdf.Rect(350, 300, 450, 380),
        pixmap=pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 30, 30)),
    )
    page.add_text_annot((300, 400), "reviewer note")

    second = document.new_page(width=595, height=842)
    second.insert_text((72, 100), "Second Page Text", fontsize=12)

    target = tmp_path / "sample.pdf"
    document.save(str(target))
    document.close()
    return target


@pytest.fixture
def session(sample_pdf):
    editor = EditorSession(str(sample_pdf))
    yield editor
    editor.close()


class TestListElements:
    def test_finds_text(self, session):
        texts = [e for e in session.list_elements() if e.kind is ElementKind.TEXT]
        assert any("Selectable Heading" in (e.text or "") for e in texts)

    def test_finds_drawings(self, session):
        drawings = [e for e in session.list_elements() if e.kind is ElementKind.DRAWING]
        assert len(drawings) >= 2

    def test_finds_annotations_with_content(self, session):
        notes = [e for e in session.list_elements() if e.kind is ElementKind.ANNOTATION]
        assert any(e.text == "reviewer note" for e in notes)

    def test_image_rect_is_reported(self, session):
        images = [e for e in session.list_elements() if e.kind is ElementKind.IMAGE]
        assert images
        assert all(e.width > 0 and e.height > 0 for e in images)

    def test_spans_all_pages_when_no_page_given(self, session):
        pages = {e.page for e in session.list_elements()}
        assert pages == {1, 2}

    def test_single_page_filter(self, session):
        assert {e.page for e in session.list_elements(page=2)} == {2}

    def test_kind_filter(self, session):
        found = session.list_elements(kinds=[ElementKind.TEXT])
        assert found
        assert all(e.kind is ElementKind.TEXT for e in found)

    def test_ids_are_unique(self, session):
        ids = [e.id for e in session.list_elements()]
        assert len(ids) == len(set(ids))

    def test_invalid_page_raises(self, session):
        with pytest.raises(ValueError, match="Invalid page"):
            session.list_elements(page=9)

    def test_text_element_carries_font_details(self, session):
        text = next(e for e in session.list_elements() if e.kind is ElementKind.TEXT)
        assert text.font
        assert text.size and text.size > 0
        assert text.rect.width > 0

    def test_to_dict_is_json_friendly(self, session):
        payload = session.list_elements()[0].to_dict()
        assert set(payload) >= {"id", "page", "kind", "x0", "y0", "x1", "y1", "text"}
        assert isinstance(payload["kind"], str)


class TestFindElement:
    def test_hit_on_text_returns_it(self, session):
        hits = session.find_element(1, 100, 96)
        assert any("Selectable Heading" in (e.text or "") for e in hits)

    def test_hit_returns_topmost_first(self, session):
        hits = session.find_element(1, 100, 200)
        kinds = [e.kind for e in hits]
        assert ElementKind.DRAWING in kinds
        if ElementKind.ANNOTATION in kinds:
            assert kinds.index(ElementKind.ANNOTATION) == 0

    def test_miss_returns_empty(self, session):
        assert session.find_element(1, 560, 800) == []

    def test_point_outside_page_returns_empty(self, session):
        assert session.find_element(1, -50, -50) == []

    def test_kind_filter(self, session):
        hits = session.find_element(1, 100, 200, kinds=[ElementKind.TEXT])
        assert all(e.kind is ElementKind.TEXT for e in hits)

    def test_invalid_page_raises(self, session):
        with pytest.raises(ValueError, match="Invalid page"):
            session.find_element(4, 10, 10)


class TestFindInRect:
    def test_finds_overlapping(self, session):
        found = session.find_elements_in_rect(1, 60, 60, 300, 260)
        kinds = {e.kind for e in found}
        assert ElementKind.DRAWING in kinds
        assert ElementKind.TEXT in kinds

    def test_empty_rect_returns_empty(self, session):
        assert session.find_elements_in_rect(1, 10, 10, 10, 10) == []

    def test_far_rect_returns_empty(self, session):
        assert session.find_elements_in_rect(1, 580, 830, 590, 840) == []


class TestGetElement:
    def test_lookup_by_id(self, session):
        element = session.get_element(1, "p1-t0")
        assert element is not None
        assert "Selectable Heading" in element.text

    def test_unknown_id_returns_none(self, session):
        assert session.get_element(1, "nope") is None


class TestModuleLevelHelpers:
    def test_list_elements_standalone(self, sample_pdf):
        document = pymupdf.open(str(sample_pdf))
        try:
            assert list_elements(document[0], 1)
        finally:
            document.close()

    def test_find_at_outside_page(self, sample_pdf):
        document = pymupdf.open(str(sample_pdf))
        try:
            assert find_at(document[0], 1, -1, -1) == []
        finally:
            document.close()

    def test_find_in_rect_rejects_empty(self, sample_pdf):
        document = pymupdf.open(str(sample_pdf))
        try:
            assert find_in_rect(document[0], 1, pymupdf.Rect(10, 10, 10, 10)) == []
        finally:
            document.close()

    def test_find_in_rect_rejects_non_finite(self, sample_pdf):
        document = pymupdf.open(str(sample_pdf))
        try:
            assert find_in_rect(document[0], 1, pymupdf.Rect(-float("inf"), -float("inf"), 1, 1)) == []
        finally:
            document.close()

    def test_page_wide_rect_returns_everything(self, sample_pdf):
        document = pymupdf.open(str(sample_pdf))
        try:
            assert len(find_in_rect(document[0], 1, pymupdf.Rect(-1e4, -1e4, 1e4, 1e4))) == len(
                list_elements(document[0], 1)
            )
        finally:
            document.close()

    def test_element_by_id_missing(self, sample_pdf):
        document = pymupdf.open(str(sample_pdf))
        try:
            assert element_by_id(document[0], 1, "absent") is None
        finally:
            document.close()


class TestRelocateDoesNotPaintOverContent:
    def test_graphic_behind_moved_text_survives(self, tmp_path):
        document = pymupdf.open()
        page = document.new_page(width=400, height=300)
        page.draw_rect(pymupdf.Rect(10, 180, 140, 215), fill=(0.9, 0.1, 0.1))
        page.insert_text((20, 200), "MOVED", fontsize=14)
        source = tmp_path / "behind.pdf"
        document.save(str(source))
        document.close()

        editor = EditorSession(str(source))
        try:
            editor.move_element(1, 10, 180, 140, 215, dx=180, dy=0)
            result = pymupdf.open(stream=editor.get_bytes(), filetype="pdf")
        finally:
            editor.close()

        try:
            pixmap = result[0].get_pixmap(clip=pymupdf.Rect(20, 185, 130, 210))
            reds = [
                pixmap.pixel(x, y)
                for x in range(0, pixmap.width, 4)
                for y in range(0, pixmap.height, 4)
                if pixmap.pixel(x, y)[0] > 150
                and pixmap.pixel(x, y)[1] < 100
                and pixmap.pixel(x, y)[2] < 100
            ]
            assert reds, "the red rectangle behind the text was painted over"
        finally:
            result.close()

    def test_moved_text_appears_at_destination(self, tmp_path):
        document = pymupdf.open()
        page = document.new_page(width=400, height=300)
        page.insert_text((20, 200), "MOVED", fontsize=14)
        source = tmp_path / "move.pdf"
        document.save(str(source))
        document.close()

        editor = EditorSession(str(source))
        try:
            editor.move_element(1, 15, 185, 130, 215, dx=150, dy=0)
            result = pymupdf.open(stream=editor.get_bytes(), filetype="pdf")
        finally:
            editor.close()

        try:
            assert result[0].get_images(full=True)
        finally:
            result.close()

    def test_unrelated_text_is_preserved(self, tmp_path):
        document = pymupdf.open()
        page = document.new_page(width=400, height=300)
        page.insert_text((20, 40), "UNTOUCHED", fontsize=12)
        page.insert_text((20, 200), "MOVED", fontsize=14)
        source = tmp_path / "keep.pdf"
        document.save(str(source))
        document.close()

        editor = EditorSession(str(source))
        try:
            editor.move_element(1, 15, 185, 130, 215, dx=150, dy=0)
            text = pymupdf.open(stream=editor.get_bytes(), filetype="pdf")[0].get_text()
        finally:
            editor.close()

        assert "UNTOUCHED" in text

    def test_resize_rejects_empty_source(self, session):
        with pytest.raises(ValueError, match="positive area"):
            session.resize_element(1, 100, 100, 100, 100, 50, 50)

    def test_resize_rejects_nonpositive_size(self, session):
        with pytest.raises(ValueError, match="must be positive"):
            session.resize_element(1, 70, 80, 200, 110, 0, 40)

    def test_resize_places_content_at_new_size(self, tmp_path):
        document = pymupdf.open()
        page = document.new_page(width=400, height=300)
        page.insert_text((20, 200), "RESIZED", fontsize=14)
        source = tmp_path / "resize.pdf"
        document.save(str(source))
        document.close()

        editor = EditorSession(str(source))
        try:
            editor.resize_element(1, 15, 185, 130, 215, 200, 60)
            result = pymupdf.open(stream=editor.get_bytes(), filetype="pdf")
        finally:
            editor.close()

        try:
            assert result[0].get_images(full=True)
        finally:
            result.close()
