import sys
from pathlib import Path

import pymupdf
import pytest
from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.docome.commands.thumbnail import pdf_app

runner = CliRunner()
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def sample_pdf(tmp_path):
    document = pymupdf.open()
    for index in range(3):
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Page {index + 1}", fontsize=24)
    target = tmp_path / "doc.pdf"
    document.save(str(target))
    document.close()
    return target


class TestThumbnailCommand:
    def test_single_page_to_file(self, sample_pdf, tmp_path):
        output = tmp_path / "page.png"
        result = runner.invoke(
            pdf_app, ["thumbnail", str(sample_pdf), "-o", str(output), "--pages", "2"]
        )
        assert result.exit_code == 0
        assert output.is_file()
        assert output.read_bytes().startswith(PNG_MAGIC)

    def test_all_pages_to_directory(self, sample_pdf, tmp_path):
        output = tmp_path / "thumbs"
        result = runner.invoke(pdf_app, ["thumbnail", str(sample_pdf), "-o", str(output)])
        assert result.exit_code == 0
        assert sorted(p.name for p in output.iterdir()) == [
            "doc-p1.png",
            "doc-p2.png",
            "doc-p3.png",
        ]

    def test_jpeg_format(self, sample_pdf, tmp_path):
        output = tmp_path / "thumbs"
        result = runner.invoke(
            pdf_app,
            ["thumbnail", str(sample_pdf), "-o", str(output), "--format", "jpeg", "--pages", "1"],
        )
        assert result.exit_code == 0
        assert (output / "doc-p1.jpeg").read_bytes().startswith(b"\xff\xd8\xff")

    def test_multiple_pages_to_image_path_fails_clearly(self, sample_pdf, tmp_path):
        output = tmp_path / "page.png"
        result = runner.invoke(pdf_app, ["thumbnail", str(sample_pdf), "-o", str(output)])
        assert result.exit_code == 1
        assert "Pass a directory instead" in result.output
        assert not output.exists()

    def test_creates_missing_parent_directory(self, sample_pdf, tmp_path):
        output = tmp_path / "nested" / "deep" / "page.png"
        result = runner.invoke(
            pdf_app, ["thumbnail", str(sample_pdf), "-o", str(output), "--pages", "1"]
        )
        assert result.exit_code == 0
        assert output.is_file()

    def test_invalid_page_fails(self, sample_pdf, tmp_path):
        result = runner.invoke(
            pdf_app, ["thumbnail", str(sample_pdf), "-o", str(tmp_path / "x"), "--pages", "9"]
        )
        assert result.exit_code == 1
        assert "Invalid page" in result.output

    def test_invalid_format_fails(self, sample_pdf, tmp_path):
        result = runner.invoke(
            pdf_app,
            ["thumbnail", str(sample_pdf), "-o", str(tmp_path / "x"), "--format", "tiff"],
        )
        assert result.exit_code == 1
        assert "format must be one of" in result.output

    def test_malformed_pages_fails(self, sample_pdf, tmp_path):
        result = runner.invoke(
            pdf_app, ["thumbnail", str(sample_pdf), "-o", str(tmp_path / "x"), "--pages", "one"]
        )
        assert result.exit_code == 1

    def test_missing_file_fails(self, tmp_path):
        result = runner.invoke(
            pdf_app, ["thumbnail", str(tmp_path / "nope.pdf"), "-o", str(tmp_path / "x")]
        )
        assert result.exit_code == 1


class TestSizesCommand:
    def test_table_output(self, sample_pdf):
        result = runner.invoke(pdf_app, ["sizes", str(sample_pdf)])
        assert result.exit_code == 0
        assert "169" in result.output and "240" in result.output

    def test_json_output(self, sample_pdf):
        import json

        result = runner.invoke(pdf_app, ["sizes", str(sample_pdf), "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert [entry["page"] for entry in payload] == [1, 2, 3]
        assert payload[0]["width"] < payload[0]["height"]

    def test_missing_file_fails(self, tmp_path):
        assert runner.invoke(pdf_app, ["sizes", str(tmp_path / "nope.pdf")]).exit_code == 1
