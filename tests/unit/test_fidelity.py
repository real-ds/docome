import io

import pymupdf
import pytest
from docx import Document

from packages.conversion_engine.fidelity import (
    ConversionFidelity,
    FidelityReport,
    evaluate,
    font_key,
    tokenize,
)
from packages.conversion_engine.reconstruction import pdf_to_docx_hq

PAGE_WIDTH = 595.0
PAGE_HEIGHT = 842.0


def _png_bytes():
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (48, 32), (200, 40, 40)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def reference_pdf(tmp_path):
    document = pymupdf.open()
    page = document.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    page.insert_text((72, 120), "Quarterly Operations Report", fontname="hebo", fontsize=18)
    page.insert_text((72, 160), "Revenue increased across all regions this quarter.", fontname="helv", fontsize=11)
    page.insert_text((72, 200), "\u2022 Asia Pacific region", fontname="helv", fontsize=11)
    page.insert_text((72, 220), "1. Europe region", fontname="helv", fontsize=11)
    page.insert_text((72, 300), "Project dashboard", fontname="helv", fontsize=11)
    page.insert_link({
        "kind": pymupdf.LINK_URI,
        "from": pymupdf.Rect(70, 290, 170, 304),
        "uri": "https://example.com/dashboard",
    })

    page.draw_rect(pymupdf.Rect(72, 360, 523, 420))
    page.draw_line(pymupdf.Point(72, 390), pymupdf.Point(523, 390))
    page.draw_line(pymupdf.Point(300, 360), pymupdf.Point(300, 420))
    page.insert_text((80, 380), "Metric", fontname="hebo", fontsize=10)
    page.insert_text((310, 380), "Value", fontname="hebo", fontsize=10)
    page.insert_text((80, 410), "Revenue", fontname="helv", fontsize=10)
    page.insert_text((310, 410), "1200", fontname="helv", fontsize=10)

    page.insert_image(pymupdf.Rect(72, 450, 200, 520), stream=_png_bytes())
    page.insert_text((72, 560), "Confidential draft", fontname="helv", fontsize=8)
    page.insert_text((300, 815), "Page 1", fontname="helv", fontsize=8)

    path = tmp_path / "reference.pdf"
    document.save(str(path))
    document.close()
    return path


@pytest.fixture
def converted_docx(reference_pdf, tmp_path):
    output = tmp_path / "converted.docx"
    pdf_to_docx_hq(str(reference_pdf), str(output))
    return output


class TestHelpers:
    def test_tokenize_lowercases_and_splits(self):
        assert tokenize("Hello, World! 42") == {"hello", "world", "42"}

    def test_tokenize_ignores_punctuation_only(self):
        assert tokenize("\u2022 \u2014") == set()

    def test_font_key_normalizes(self):
        assert font_key("Arial", 11.04) == "arial|11.0"
        assert font_key("Arial", 11.0) == font_key("arial", 11.0)


class TestFidelityReport:
    def test_score_is_one_when_nothing_to_preserve(self):
        report = FidelityReport(
            source_pages=1, output_sections=1, text_retention=1.0, font_retention=1.0,
            tables_source=0, tables_output=0, images_source=0, images_output=0,
            hyperlinks_source=0, hyperlinks_output=0,
        )
        assert report.score == 1.0
        assert report.passed is True

    def test_page_mismatch_fails(self):
        report = FidelityReport(
            source_pages=3, output_sections=1, text_retention=1.0, font_retention=1.0,
            tables_source=0, tables_output=0, images_source=0, images_output=0,
            hyperlinks_source=0, hyperlinks_output=0,
        )
        assert report.page_count_preserved is False
        assert report.passed is False

    def test_ratio_caps_at_one(self):
        assert FidelityReport._ratio(5, 2) == 1.0
        assert FidelityReport._ratio(1, 2) == 0.5

    def test_as_dict_exposes_metrics(self):
        report = FidelityReport(
            source_pages=1, output_sections=1, text_retention=0.95, font_retention=1.0,
            tables_source=1, tables_output=1, images_source=1, images_output=1,
            hyperlinks_source=1, hyperlinks_output=1,
        )
        payload = report.as_dict()
        assert payload["text_retention"] == 0.95
        assert payload["tables"] == "1/1"
        assert payload["passed"] is True

    def test_missing_tokens_are_reported(self):
        report = FidelityReport(
            source_pages=1, output_sections=1, text_retention=0.5, font_retention=1.0,
            tables_source=0, tables_output=0, images_source=0, images_output=0,
            hyperlinks_source=0, hyperlinks_output=0, missing_text=["alpha"],
        )
        assert report.as_dict()["missing_text"] == ["alpha"]


class TestConversionFidelity:
    def test_page_count_is_preserved(self, reference_pdf, converted_docx):
        report = evaluate(reference_pdf, converted_docx)
        assert report.source_pages == 1
        assert report.page_count_preserved is True

    def test_text_retention_meets_threshold(self, reference_pdf, converted_docx):
        report = evaluate(reference_pdf, converted_docx)
        assert report.text_retention >= 0.9
        assert "revenue" not in report.missing_text

    def test_all_body_text_is_recovered(self, reference_pdf, converted_docx):
        report = evaluate(reference_pdf, converted_docx)
        source = tokenize(pymupdf.open(str(reference_pdf))[0].get_text())
        missing = {token for token in source if token not in report.missing_text}
        assert "quarterly" in missing
        assert "confidential" in missing

    def test_fonts_are_preserved(self, reference_pdf, converted_docx):
        report = evaluate(reference_pdf, converted_docx)
        assert report.font_retention >= 0.9

    def test_table_is_preserved(self, reference_pdf, converted_docx):
        report = evaluate(reference_pdf, converted_docx)
        assert report.tables_source == 1
        assert report.tables_preserved is True

    def test_image_is_preserved(self, reference_pdf, converted_docx):
        report = evaluate(reference_pdf, converted_docx)
        assert report.images_source == 1
        assert report.images_preserved is True

    def test_hyperlink_is_preserved(self, reference_pdf, converted_docx):
        report = evaluate(reference_pdf, converted_docx)
        assert report.hyperlinks_source == 1
        assert report.hyperlinks_preserved is True

    def test_overall_report_passes(self, reference_pdf, converted_docx):
        report = evaluate(reference_pdf, converted_docx)
        assert report.passed is True
        assert report.score >= 0.9

    def test_header_text_counted_from_sections(self, reference_pdf, converted_docx):
        report = evaluate(reference_pdf, converted_docx)
        assert "confidential" not in report.missing_text

    def test_missing_content_lowers_score(self, reference_pdf, tmp_path):
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        document = Document()
        document.add_paragraph("Totally different content")
        stripped = tmp_path / "stripped.docx"
        document.save(str(stripped))

        report = ConversionFidelity().evaluate(reference_pdf, stripped)
        assert report.text_retention < 0.5
        assert report.passed is False

    def test_multi_page_reports_each_page(self, tmp_path):
        source = pymupdf.open()
        for index in range(2):
            page = source.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
            page.insert_text((72, 140), f"Chapter {index + 1} body text", fontname="helv", fontsize=12)
        pdf_path = tmp_path / "chapters.pdf"
        source.save(str(pdf_path))
        source.close()

        docx_path = tmp_path / "chapters.docx"
        pdf_to_docx_hq(str(pdf_path), str(docx_path))

        report = evaluate(pdf_path, docx_path)
        assert report.source_pages == 2
        assert report.output_sections == 2
        assert report.page_count_preserved is True
        assert report.text_retention >= 0.9

    def test_report_is_json_serializable(self, reference_pdf, converted_docx):
        import json

        report = evaluate(reference_pdf, converted_docx)
        payload = json.loads(json.dumps(report.as_dict()))
        assert payload["score"] == report.score
