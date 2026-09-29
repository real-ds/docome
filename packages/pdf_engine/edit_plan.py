import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from .editor import AnnotationType, EditorSession, ShapeType


class EditPlanError(ValueError):
    def __init__(self, message: str, index: Optional[int] = None):
        if index is not None:
            message = f"operation {index}: {message}"
        super().__init__(message)
        self.index = index


@dataclass
class EditResult:
    output_path: Optional[str] = None
    applied: List[str] = field(default_factory=list)
    undo_steps: int = 0
    redo_steps: int = 0

    @property
    def operation_count(self) -> int:
        return len(self.applied)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "output_path": self.output_path,
            "applied": list(self.applied),
            "operation_count": self.operation_count,
            "undo_steps": self.undo_steps,
            "redo_steps": self.redo_steps,
        }


class EditPlan:
    def __init__(self, operations: Sequence[Dict[str, Any]]):
        self.operations: List[Dict[str, Any]] = [
            dict(operation) if isinstance(operation, dict) else operation
            for operation in operations
        ]

    @classmethod
    def from_json(cls, payload: Union[str, bytes]) -> "EditPlan":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as error:
            raise EditPlanError(f"invalid JSON: {error}") from error

        if isinstance(data, list):
            operations = data
        elif isinstance(data, dict):
            operations = data.get("operations", [])
        else:
            raise EditPlanError("plan must be a list of operations or an object with 'operations'")

        if not isinstance(operations, list):
            raise EditPlanError("'operations' must be a list")

        return cls(operations)

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "EditPlan":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


class EditPlanExecutor:
    ACTIONS = (
        "add_text",
        "delete_text",
        "replace_text",
        "add_image",
        "draw_shape",
        "add_annotation",
        "move",
        "resize",
        "undo",
        "redo",
    )

    def __init__(self):
        self._handlers: Dict[str, Callable[[EditorSession, Dict[str, Any]], str]] = {
            "add_text": self._add_text,
            "delete_text": self._delete_text,
            "replace_text": self._replace_text,
            "add_image": self._add_image,
            "draw_shape": self._draw_shape,
            "add_annotation": self._add_annotation,
            "move": self._move,
            "resize": self._resize,
            "undo": self._undo,
            "redo": self._redo,
        }

    def available_actions(self) -> List[str]:
        return list(self.ACTIONS)

    def apply(
        self,
        input_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
        plan: Union[EditPlan, Sequence[Dict[str, Any]]],
    ) -> EditResult:
        if not isinstance(plan, EditPlan):
            plan = EditPlan(plan)

        session = EditorSession(input_path)
        result = EditResult(output_path=str(output_path))
        try:
            for index, operation in enumerate(plan.operations):
                result.applied.append(self._run(session, operation, index))
            result.undo_steps = session.undo_depth
            result.redo_steps = session.redo_depth
            session.save(output_path)
        finally:
            session.close()
        return result

    def _run(self, session: EditorSession, operation: Dict[str, Any], index: int) -> str:
        if not isinstance(operation, dict):
            raise EditPlanError("operation must be an object", index)

        action = operation.get("action")
        if not action:
            raise EditPlanError("missing 'action'", index)

        handler = self._handlers.get(action)
        if handler is None:
            raise EditPlanError(f"unknown action '{action}'", index)

        params = {key: value for key, value in operation.items() if key != "action"}
        try:
            return handler(session, params)
        except EditPlanError:
            raise
        except (ValueError, TypeError, KeyError, FileNotFoundError) as error:
            raise EditPlanError(str(error), index) from error

    def _add_text(self, session: EditorSession, params: Dict[str, Any]) -> str:
        session.add_text(
            page=self._page(params),
            x=self._number(params, "x"),
            y=self._number(params, "y"),
            text=self._text(params, "text"),
            fontsize=self._number(params, "fontsize", default=12.0),
            fontname=self._string(params, "fontname", default="helv"),
            color=self._color(params, default=(0, 0, 0)),
        )
        return "add_text"

    def _delete_text(self, session: EditorSession, params: Dict[str, Any]) -> str:
        rect = self._rect(params)
        session.delete_text(page=self._page(params), **rect)
        return "delete_text"

    def _replace_text(self, session: EditorSession, params: Dict[str, Any]) -> str:
        rect = self._rect(params)
        session.replace_text(
            page=self._page(params),
            new_text=self._text(params, "new_text"),
            fontsize=self._number(params, "fontsize", default=12.0),
            fontname=self._string(params, "fontname", default="helv"),
            color=self._color(params, default=(0, 0, 0)),
            **rect,
        )
        return "replace_text"

    def _add_image(self, session: EditorSession, params: Dict[str, Any]) -> str:
        session.add_image(
            page=self._page(params),
            image_data=self._image_bytes(params),
            x=self._number(params, "x"),
            y=self._number(params, "y"),
            width=self._optional_number(params, "width"),
            height=self._optional_number(params, "height"),
        )
        return "add_image"

    def _draw_shape(self, session: EditorSession, params: Dict[str, Any]) -> str:
        rect = self._rect(params)
        session.draw_shape(
            page=self._page(params),
            shape_type=self._enum(ShapeType, params, "shape_type", default="RECT"),
            color=self._color(params, default=(0, 0, 0)),
            fill=self._optional_color(params, "fill"),
            width=self._number(params, "line_width", default=1.0),
            **rect,
        )
        return "draw_shape"

    def _add_annotation(self, session: EditorSession, params: Dict[str, Any]) -> str:
        rect = self._rect(params)
        session.add_annotation(
            page=self._page(params),
            annot_type=self._enum(AnnotationType, params, "annotation", default="HIGHLIGHT"),
            text=self._string(params, "text", default=""),
            color=self._color(params, default=(1, 1, 0)),
            **rect,
        )
        return "add_annotation"

    def _move(self, session: EditorSession, params: Dict[str, Any]) -> str:
        rect = self._rect(params)
        session.move_element(
            page=self._page(params),
            dx=self._number(params, "dx"),
            dy=self._number(params, "dy"),
            **rect,
        )
        return "move"

    def _resize(self, session: EditorSession, params: Dict[str, Any]) -> str:
        rect = self._rect(params)
        session.resize_element(
            page=self._page(params),
            width=self._number(params, "width"),
            height=self._number(params, "height"),
            **rect,
        )
        return "resize"

    def _undo(self, session: EditorSession, params: Dict[str, Any]) -> str:
        count = self._number(params, "times", default=1.0)
        for _ in range(max(1, int(count))):
            if not session.undo():
                raise EditPlanError("nothing left to undo")
        return "undo"

    def _redo(self, session: EditorSession, params: Dict[str, Any]) -> str:
        count = self._number(params, "times", default=1.0)
        for _ in range(max(1, int(count))):
            if not session.redo():
                raise EditPlanError("nothing left to redo")
        return "redo"

    def _page(self, params: Dict[str, Any]) -> int:
        if "page" not in params:
            raise EditPlanError("missing 'page'")
        try:
            return int(params["page"])
        except (TypeError, ValueError) as error:
            raise EditPlanError("'page' must be an integer") from error

    def _rect(self, params: Dict[str, Any]) -> Dict[str, float]:
        rect = params.get("rect")
        source = rect if isinstance(rect, dict) else params
        return {
            "x0": self._number(source, "x0"),
            "y0": self._number(source, "y0"),
            "x1": self._number(source, "x1"),
            "y1": self._number(source, "y1"),
        }

    def _number(self, params: Dict[str, Any], key: str, default: Optional[float] = None) -> float:
        if key not in params or params[key] is None:
            if default is None:
                raise EditPlanError(f"missing '{key}'")
            return float(default)
        try:
            return float(params[key])
        except (TypeError, ValueError) as error:
            raise EditPlanError(f"'{key}' must be a number") from error

    def _optional_number(self, params: Dict[str, Any], key: str) -> Optional[float]:
        if key not in params or params[key] is None:
            return None
        return self._number(params, key, default=0.0)

    def _text(self, params: Dict[str, Any], key: str) -> str:
        value = params.get(key)
        if not isinstance(value, str) or not value:
            raise EditPlanError(f"missing or empty '{key}'")
        return value

    def _string(self, params: Dict[str, Any], key: str, default: str = "") -> str:
        value = params.get(key)
        if value is None:
            return default
        if not isinstance(value, str):
            raise EditPlanError(f"'{key}' must be a string")
        return value

    def _color(self, params: Dict[str, Any], key: str = "color", default=(0, 0, 0)) -> Tuple[float, float, float]:
        value = params.get(key)
        if value is None:
            return tuple(default)
        return self._coerce_color(value, key)

    def _optional_color(self, params: Dict[str, Any], key: str) -> Optional[Tuple[float, float, float]]:
        value = params.get(key)
        if value is None:
            return None
        return self._coerce_color(value, key)

    def _coerce_color(self, value: Any, key: str) -> Tuple[float, float, float]:
        if isinstance(value, (list, tuple)) and len(value) == 3:
            try:
                return tuple(float(channel) for channel in value)  # type: ignore[return-value]
            except (TypeError, ValueError) as error:
                raise EditPlanError(f"'{key}' channels must be numbers") from error
        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",")]
            if len(parts) == 3:
                try:
                    return tuple(float(part) for part in parts)  # type: ignore[return-value]
                except ValueError as error:
                    raise EditPlanError(f"'{key}' must be r,g,b numbers") from error
        raise EditPlanError(f"'{key}' must be [r, g, b] or 'r,g,b'")

    def _enum(self, enum_class, params: Dict[str, Any], key: str, default: str):
        raw = params.get(key, default)
        if isinstance(raw, enum_class):
            return raw
        if not isinstance(raw, str):
            raise EditPlanError(f"'{key}' must be a string")
        try:
            return enum_class[raw.strip().upper()]
        except KeyError as error:
            allowed = ", ".join(member.name for member in enum_class)
            raise EditPlanError(f"'{key}' must be one of: {allowed}") from error

    def _image_bytes(self, params: Dict[str, Any]) -> bytes:
        if "image_base64" in params and params["image_base64"]:
            import base64

            try:
                return base64.b64decode(params["image_base64"])
            except Exception as error:
                raise EditPlanError("'image_base64' is not valid base64") from error

        path = params.get("image_path")
        if not isinstance(path, str) or not path:
            raise EditPlanError("missing 'image_path' or 'image_base64'")
        data = Path(path).read_bytes()
        if not data:
            raise EditPlanError(f"image file is empty: {path}")
        return data


def apply_edit_plan(
    input_path: Union[str, Path, bytes],
    output_path: Union[str, Path],
    operations: Union[EditPlan, Sequence[Dict[str, Any]]],
) -> EditResult:
    return EditPlanExecutor().apply(input_path, output_path, operations)
