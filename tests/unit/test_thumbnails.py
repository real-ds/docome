import sys
from pathlib import Path

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from packages.pdf_engine import PageImage, render_page, render_pages, thumbnail_size
from packages.pdf_engine.thumbnails import MAX_DPI, MIN_DPI

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


@pytest.fixture
def sample_pdf(tmp_path):
    document = pymupdf.open()
    for index in range(3):
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Page {index + 1}", fontsize=24)
    target = tmp_path / "pages.pdf"
    document.save(str(target))
    document.close()
    return target


def test_dpi_is_clamped_to_integers(sample_pdf):
    image = render_page(str(sample_pdf), 1, dpi=72.6)
    assert image.dpi == 73


class TestRenderPage:
    def test_returns_encoded_png(self, sample_pdf):
        image = render_page(str(sample_pdf), 1, dpi=72)
        assert image.data.startswith(PNG_MAGIC)
        assert image.media_type == "image/png"

    def test_dimensions_follow_dpi(self, sample_pdf):
        low = render_page(str(sample_pdf), 1, dpi=36)
        high = render_page(str(sample_pdf), 1, dpi=72)
        assert high.width == pytest.approx(low.width * 2, rel=0.05)
        assert high.height == pytest.approx(low.height * 2, rel=0.05)

    def test_aspect_ratio_preserved(self, sample_pdf):
        image = render_page(str(sample_pdf), 1, dpi=72)
        assert image.width / image.height == pytest.approx(595 / 842, rel=0.02)

    def test_default_is_a_thumbnail(self, sample_pdf):
        assert render_page(str(sample_pdf), 1).width <= 240

    def test_accepts_bytes(self, sample_pdf):
        image = render_page(sample_pdf.read_bytes(), 2, dpi=36)
        assert image.page == 2
        assert image.data.startswith(PNG_MAGIC)

    def test_jpeg_format(self, sample_pdf):
        image = render_page(str(sample_pdf), 1, dpi=72, image_format="jpeg")
        assert image.data.startswith(JPEG_MAGIC)
        assert image.media_type == "image/jpeg"

    def test_jpg_alias(self, sample_pdf):
        assert render_page(str(sample_pdf), 1, image_format="jpg").media_type == "image/jpeg"

    def test_format_is_case_insensitive(self, sample_pdf):
        assert render_page(str(sample_pdf), 1, image_format="PNG").media_type == "image/png"

    def test_rejects_bad_page(self, sample_pdf):
        with pytest.raises(ValueError, match="Invalid page"):
            render_page(str(sample_pdf), 99)

    def test_rejects_page_zero(self, sample_pdf):
        with pytest.raises(ValueError, match="Invalid page"):
            render_page(str(sample_pdf), 0)

    def test_rejects_low_dpi(self, sample_pdf):
        with pytest.raises(ValueError, match="at least"):
            render_page(str(sample_pdf), 1, dpi=MIN_DPI - 1)

    def test_rejects_high_dpi(self, sample_pdf):
        with pytest.raises(ValueError, match="at most"):
            render_page(str(sample_pdf), 1, dpi=MAX_DPI + 1)

    def test_rejects_nan_dpi(self, sample_pdf):
        with pytest.raises(ValueError, match="finite"):
            render_page(str(sample_pdf), 1, dpi=float("nan"))

    def test_rejects_infinite_dpi(self, sample_pdf):
        with pytest.raises(ValueError, match="finite"):
            render_page(str(sample_pdf), 1, dpi=float("inf"))

    def test_rejects_unknown_format(self, sample_pdf):
        with pytest.raises(ValueError, match="format must be one of"):
            render_page(str(sample_pdf), 1, image_format="tiff")

    def test_rejects_non_pdf_bytes(self):
        with pytest.raises(Exception):
            render_page(b"this is not a pdf", 1)

    def test_to_dict(self, sample_pdf):
        payload = render_page(str(sample_pdf), 1, dpi=36).to_dict()
        assert payload["page"] == 1
        assert payload["media_type"] == "image/png"
        assert payload["bytes"] > 0


class TestRenderPages:
    def test_defaults_to_every_page(self, sample_pdf):
        assert [image.page for image in render_pages(str(sample_pdf), dpi=36)] == [1, 2, 3]

    def test_subset(self, sample_pdf):
        assert [image.page for image in render_pages(str(sample_pdf), [2], dpi=36)] == [2]

    def test_order_follows_request(self, sample_pdf):
        assert [image.page for image in render_pages(str(sample_pdf), [3, 1], dpi=36)] == [3, 1]

    def test_empty_list_means_all(self, sample_pdf):
        assert len(render_pages(str(sample_pdf), [], dpi=36)) == 3

    def test_rejects_out_of_range_page(self, sample_pdf):
        with pytest.raises(ValueError, match="Invalid page"):
            render_pages(str(sample_pdf), [1, 7], dpi=36)

    def test_rejects_bad_format(self, sample_pdf):
        with pytest.raises(ValueError, match="format must be one of"):
            render_pages(str(sample_pdf), [1], image_format="bmp")

    def test_every_page_renders_distinctly(self, sample_pdf):
        pages = render_pages(str(sample_pdf), dpi=36)
        assert len({image.data for image in pages}) == 3


class TestThumbnailSize:
    def test_fits_within_max_dimension(self, sample_pdf):
        for page, (width, height) in thumbnail_size(str(sample_pdf), 240):
            assert max(width, height) <= 240
            assert min(width, height) > 0

    def test_keeps_aspect_ratio(self, sample_pdf):
        for _, (width, height) in thumbnail_size(str(sample_pdf), 240):
            assert width / height == pytest.approx(595 / 842, rel=0.02)

    def test_never_upscales(self, sample_pdf):
        for _, (width, height) in thumbnail_size(str(sample_pdf), 4000):
            assert width <= 595 and height <= 842

    def test_one_entry_per_page(self, sample_pdf):
        assert [page for page, _ in thumbnail_size(str(sample_pdf))] == [1, 2, 3]

    def test_rejects_non_positive(self, sample_pdf):
        with pytest.raises(ValueError, match="must be positive"):
            thumbnail_size(str(sample_pdf), 0)


class TestPageImageModel:
    def test_fields(self):
        image = PageImage(
            page=2, width=10, height=20, dpi=36, media_type="image/png", data=b"abc"
        )
        assert image.to_dict() == {
            "page": 2,
            "width": 10,
            "height": 20,
            "dpi": 36,
            "media_type": "image/png",
            "bytes": 3,
        }
