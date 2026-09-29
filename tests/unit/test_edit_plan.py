import base64
import io
import json

import pymupdf
import pytest

from packages.pdf_engine import (
    EditPlan,
    EditPlanError,
    EditPlanExecutor,
    EditorSession,
    apply_edit_plan,
)
from packages.pdf_engine.edit_plan import EditResult


def make_pdf(path, pages=2, text="Original content"):
    document = pymupdf.open()
    for _ in range(pages):
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 100), text, fontname="helv", fontsize=12)
    document.save(str(path))
    document.close()
    return path


def png_bytes():
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), (10, 200, 90)).save(buffer, format="PNG")
    return buffer.getvalue()


def text_of(path):
    document = pymupdf.open(str(path))
    try:
        return "\n".join(page.get_text() for page in document)
    finally:
        document.close()


@pytest.fixture
def source_pdf(tmp_path):
    return make_pdf(tmp_path / "source.pdf")


class TestEditPlanParsing:
    def test_from_json_list(self):
        plan = EditPlan.from_json('[{"action": "add_text"}]')
        assert len(plan.operations) == 1

    def test_from_json_object_with_operations(self):
        plan = EditPlan.from_json('{"operations": [{"action": "undo"}]}')
        assert plan.operations[0]["action"] == "undo"

    def test_from_json_invalid(self):
        with pytest.raises(EditPlanError, match="invalid JSON"):
            EditPlan.from_json("{not json")

    def test_from_json_wrong_type(self):
        with pytest.raises(EditPlanError, match="must be a list"):
            EditPlan.from_json('"just a string"')

    def test_from_json_operations_not_list(self):
        with pytest.raises(EditPlanError, match="must be a list"):
            EditPlan.from_json('{"operations": 5}')

    def test_from_file(self, tmp_path):
        path = tmp_path / "plan.json"
        path.write_text(json.dumps([{"action": "add_text", "page": 1}]), encoding="utf-8")
        plan = EditPlan.from_file(path)
        assert plan.operations[0]["page"] == 1


class TestExecutorValidation:
    def test_unknown_action_rejected(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="unknown action"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"), [{"action": "fly"}])

    def test_error_reports_operation_index(self, source_pdf, tmp_path):
        plan = [{"action": "add_text", "page": 1, "x": 10, "y": 10, "text": "ok"},
                {"action": "fly"}]
        with pytest.raises(EditPlanError) as error:
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"), plan)
        assert "operation 1" in str(error.value)
        assert error.value.index == 1

    def test_missing_action_rejected(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="missing 'action'"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"), [{"page": 1}])

    def test_operation_must_be_object(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="must be an object"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"), ["add_text"])

    def test_missing_page_rejected(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="missing 'page'"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"),
                            [{"action": "add_text", "x": 1, "y": 1, "text": "t"}])

    def test_non_integer_page_rejected(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="must be an integer"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"),
                            [{"action": "add_text", "page": "first", "x": 1, "y": 1, "text": "t"}])

    def test_invalid_page_number_rejected(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="Invalid page"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"),
                            [{"action": "add_text", "page": 99, "x": 1, "y": 1, "text": "t"}])

    def test_empty_text_rejected(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="missing or empty 'text'"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"),
                            [{"action": "add_text", "page": 1, "x": 1, "y": 1, "text": ""}])

    def test_missing_rect_coordinate(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="missing 'x1'"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"),
                            [{"action": "draw_shape", "page": 1, "shape_type": "RECT",
                              "x0": 10, "y0": 10, "y1": 50}])

    def test_bad_enum_value_lists_options(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="must be one of"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"),
                            [{"action": "draw_shape", "page": 1, "shape_type": "TRIANGLE",
                              "x0": 1, "y0": 1, "x1": 5, "y1": 5}])

    def test_bad_color_rejected(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="'color'"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"),
                            [{"action": "add_text", "page": 1, "x": 1, "y": 1,
                              "text": "t", "color": "purple"}])

    def test_missing_image_source_rejected(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="image_path"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"),
                            [{"action": "add_image", "page": 1, "x": 10, "y": 10}])

    def test_failed_plan_writes_no_output(self, source_pdf, tmp_path):
        output = tmp_path / "never.pdf"
        with pytest.raises(EditPlanError):
            apply_edit_plan(str(source_pdf), str(output), [{"action": "fly"}])
        assert not output.exists()


class TestApplyOperations:
    def test_add_text(self, source_pdf, tmp_path):
        output = tmp_path / "text.pdf"
        result = apply_edit_plan(str(source_pdf), str(output), [
            {"action": "add_text", "page": 1, "x": 100, "y": 300, "text": "Injected", "fontsize": 14},
        ])
        assert result.operation_count == 1
        assert "Injected" in text_of(output)

    def test_add_text_uses_requested_font(self, source_pdf, tmp_path):
        output = tmp_path / "bold.pdf"
        apply_edit_plan(str(source_pdf), str(output), [
            {"action": "add_text", "page": 1, "x": 100, "y": 300, "text": "Bold", "fontname": "hebo"},
        ])
        document = pymupdf.open(str(output))
        fonts = {
            span["font"]
            for block in document[0].get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line["spans"]
        }
        document.close()
        assert any("Bold" in font for font in fonts)

    def test_multiple_operations_in_one_session(self, source_pdf, tmp_path):
        output = tmp_path / "multi.pdf"
        result = apply_edit_plan(str(source_pdf), str(output), [
            {"action": "add_text", "page": 1, "x": 100, "y": 300, "text": "First"},
            {"action": "add_text", "page": 1, "x": 100, "y": 320, "text": "Second"},
            {"action": "add_text", "page": 2, "x": 100, "y": 300, "text": "Third"},
        ])
        text = text_of(output)
        assert result.applied == ["add_text", "add_text", "add_text"]
        assert "First" in text and "Second" in text and "Third" in text

    def test_replace_text(self, source_pdf, tmp_path):
        output = tmp_path / "replaced.pdf"
        apply_edit_plan(str(source_pdf), str(output), [
            {"action": "replace_text", "page": 1, "x0": 60, "y0": 88, "x1": 200, "y1": 104,
             "new_text": "Replaced"},
        ])
        assert "Replaced" in text_of(output)

    def test_delete_text(self, source_pdf, tmp_path):
        output = tmp_path / "deleted.pdf"
        apply_edit_plan(str(source_pdf), str(output), [
            {"action": "delete_text", "page": 1, "x0": 60, "y0": 88, "x1": 250, "y1": 104},
        ])
        document = pymupdf.open(str(output))
        page_one = document[0].get_text()
        page_two = document[1].get_text()
        document.close()
        assert "Original content" not in page_one
        assert "Original content" in page_two

    def test_rect_can_be_nested_object(self, source_pdf, tmp_path):
        output = tmp_path / "nested.pdf"
        apply_edit_plan(str(source_pdf), str(output), [
            {"action": "add_text", "page": 1, "x": 100, "y": 300, "text": "Nested",
             "rect": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}},
        ])
        assert "Nested" in text_of(output)

    def test_add_image_from_base64(self, source_pdf, tmp_path):
        output = tmp_path / "image.pdf"
        apply_edit_plan(str(source_pdf), str(output), [
            {"action": "add_image", "page": 1, "x": 100, "y": 300, "width": 80,
             "image_base64": base64.b64encode(png_bytes()).decode()},
        ])
        document = pymupdf.open(str(output))
        images = document[0].get_images()
        document.close()
        assert len(images) == 1

    def test_add_image_from_path(self, source_pdf, tmp_path):
        image_path = tmp_path / "logo.png"
        image_path.write_bytes(png_bytes())
        output = tmp_path / "image2.pdf"
        apply_edit_plan(str(source_pdf), str(output), [
            {"action": "add_image", "page": 1, "x": 100, "y": 300,
             "image_path": str(image_path)},
        ])
        document = pymupdf.open(str(output))
        assert len(document[0].get_images()) == 1
        document.close()

    def test_missing_image_file_reports_path(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="logo.png"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"), [
                {"action": "add_image", "page": 1, "x": 1, "y": 1,
                 "image_path": str(tmp_path / "logo.png")},
            ])

    def test_draw_shape_variants(self, source_pdf, tmp_path):
        output = tmp_path / "shapes.pdf"
        result = apply_edit_plan(str(source_pdf), str(output), [
            {"action": "draw_shape", "page": 1, "shape_type": "RECT",
             "x0": 50, "y0": 200, "x1": 150, "y1": 260, "color": [1, 0, 0]},
            {"action": "draw_shape", "page": 1, "shape_type": "CIRCLE",
             "x0": 200, "y0": 200, "x1": 260, "y1": 260},
            {"action": "draw_shape", "page": 1, "shape_type": "LINE",
             "x0": 50, "y0": 300, "x1": 300, "y1": 300, "line_width": 2},
        ])
        assert result.applied == ["draw_shape"] * 3
        assert output.exists()

    def test_add_annotation_variants(self, source_pdf, tmp_path):
        output = tmp_path / "annots.pdf"
        apply_edit_plan(str(source_pdf), str(output), [
            {"action": "add_annotation", "page": 1, "annotation": "HIGHLIGHT",
             "x0": 70, "y0": 90, "x1": 200, "y1": 105},
            {"action": "add_annotation", "page": 1, "annotation": "STICKY",
             "x0": 70, "y0": 120, "x1": 200, "y1": 135, "text": "note"},
        ])
        document = pymupdf.open(str(output))
        annotations = list(document[0].annots() or [])
        document.close()
        assert len(annotations) == 2

    def test_move_and_resize(self, source_pdf, tmp_path):
        output = tmp_path / "moved.pdf"
        result = apply_edit_plan(str(source_pdf), str(output), [
            {"action": "move", "page": 1, "x0": 60, "y0": 85, "x1": 250, "y1": 110,
             "dx": 20, "dy": 40},
            {"action": "resize", "page": 1, "x0": 60, "y0": 200, "x1": 200, "y1": 240,
             "width": 120, "height": 30},
        ])
        assert result.applied == ["move", "resize"]

    def test_color_accepts_csv_string(self, source_pdf, tmp_path):
        output = tmp_path / "colored.pdf"
        apply_edit_plan(str(source_pdf), str(output), [
            {"action": "add_text", "page": 1, "x": 100, "y": 300, "text": "Red",
             "color": "1,0,0"},
        ])
        document = pymupdf.open(str(output))
        colors = {
            span["color"]
            for block in document[0].get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line["spans"]
        }
        document.close()
        assert 0xFF0000 in colors

    def test_empty_plan_copies_document(self, source_pdf, tmp_path):
        output = tmp_path / "copy.pdf"
        result = apply_edit_plan(str(source_pdf), str(output), [])
        assert result.operation_count == 0
        assert "Original content" in text_of(output)

    def test_accepts_edit_plan_instance(self, source_pdf, tmp_path):
        output = tmp_path / "instance.pdf"
        plan = EditPlan([{"action": "add_text", "page": 1, "x": 10, "y": 400, "text": "P"}])
        result = apply_edit_plan(str(source_pdf), str(output), plan)
        assert result.operation_count == 1

    def test_accepts_bytes_input(self, source_pdf, tmp_path):
        output = tmp_path / "bytes.pdf"
        apply_edit_plan(source_pdf.read_bytes(), str(output), [
            {"action": "add_text", "page": 1, "x": 10, "y": 400, "text": "FromBytes"},
        ])
        assert "FromBytes" in text_of(output)


class TestUndoRedoInPlan:
    def test_undo_action_reverts_last_step(self, source_pdf, tmp_path):
        output = tmp_path / "undone.pdf"
        apply_edit_plan(str(source_pdf), str(output), [
            {"action": "add_text", "page": 1, "x": 100, "y": 300, "text": "Temporary"},
            {"action": "undo"},
        ])
        assert "Temporary" not in text_of(output)

    def test_undo_multiple_times(self, source_pdf, tmp_path):
        output = tmp_path / "undone2.pdf"
        apply_edit_plan(str(source_pdf), str(output), [
            {"action": "add_text", "page": 1, "x": 100, "y": 300, "text": "One"},
            {"action": "add_text", "page": 1, "x": 100, "y": 320, "text": "Two"},
            {"action": "undo", "times": 2},
        ])
        text = text_of(output)
        assert "One" not in text and "Two" not in text

    def test_undo_past_start_fails(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="nothing left to undo"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"), [{"action": "undo"}])

    def test_redo_action(self, source_pdf, tmp_path):
        output = tmp_path / "redone.pdf"
        apply_edit_plan(str(source_pdf), str(output), [
            {"action": "add_text", "page": 1, "x": 100, "y": 300, "text": "RedoMe"},
            {"action": "undo"},
            {"action": "redo"},
        ])
        assert "RedoMe" in text_of(output)

    def test_redo_past_end_fails(self, source_pdf, tmp_path):
        with pytest.raises(EditPlanError, match="nothing left to redo"):
            apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"), [{"action": "redo"}])

    def test_result_reports_history_depth(self, source_pdf, tmp_path):
        result = apply_edit_plan(str(source_pdf), str(tmp_path / "o.pdf"), [
            {"action": "add_text", "page": 1, "x": 10, "y": 400, "text": "A"},
            {"action": "add_text", "page": 1, "x": 10, "y": 420, "text": "B"},
        ])
        assert result.undo_steps == 2
        assert result.redo_steps == 0


class TestSessionIntrospection:
    def test_undo_and_redo_depth(self, source_pdf):
        session = EditorSession(str(source_pdf))
        assert session.undo_depth == 0
        assert session.redo_depth == 0
        session.add_text(1, 100, 300, "One")
        assert session.undo_depth == 1
        session.add_text(1, 100, 320, "Two")
        assert session.undo_depth == 2
        session.undo()
        assert session.undo_depth == 1
        assert session.redo_depth == 1
        session.close()

    def test_page_count_property(self, source_pdf):
        session = EditorSession(str(source_pdf))
        assert session.page_count == 2
        session.close()


class TestExecutorApi:
    def test_available_actions(self):
        actions = EditPlanExecutor().available_actions()
        assert "add_text" in actions
        assert "undo" in actions
        assert len(actions) == 10

    def test_result_as_dict(self):
        result = EditResult(output_path="x.pdf", applied=["add_text", "undo"], undo_steps=1)
        payload = result.as_dict()
        assert payload["operation_count"] == 2
        assert payload["applied"] == ["add_text", "undo"]
