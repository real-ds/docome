from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field, ValidationError

from app.core.workspace import PDF_MEDIA_TYPE, output_path, uploaded_file, workspace
from pdf_engine import EditPlan, EditPlanError, EditPlanExecutor, apply_edit_plan

router = APIRouter(prefix="/api/v1/edit", tags=["edit"])

MAX_OPERATIONS = 200
MAX_PLAN_BYTES = 256 * 1024


class EditOperationModel(BaseModel):
    action: str = Field(..., min_length=1)
    page: Optional[int] = Field(None, ge=1)
    x: Optional[float] = None
    y: Optional[float] = None
    x0: Optional[float] = None
    y0: Optional[float] = None
    x1: Optional[float] = None
    y1: Optional[float] = None
    text: Optional[str] = None
    new_text: Optional[str] = None
    fontsize: Optional[float] = None
    fontname: Optional[str] = None
    color: Optional[Any] = None
    fill: Optional[Any] = None
    line_width: Optional[float] = None
    shape_type: Optional[str] = None
    annotation: Optional[str] = None
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    dx: Optional[float] = None
    dy: Optional[float] = None
    times: Optional[int] = Field(None, ge=1)


class EditPlanRequest(BaseModel):
    operations: List[EditOperationModel] = Field(..., min_length=1, max_length=MAX_OPERATIONS)


def parse_plan(raw: str) -> EditPlan:
    if len(raw.encode("utf-8")) > MAX_PLAN_BYTES:
        raise HTTPException(status_code=413, detail="Edit plan is too large")

    try:
        request = EditPlanRequest.model_validate_json(raw)
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=_summarize(error))

    operations: List[Dict[str, Any]] = [
        operation.model_dump(exclude_none=True) for operation in request.operations
    ]
    return EditPlan(operations)


def _summarize(error: ValidationError) -> str:
    parts = []
    for item in error.errors()[:5]:
        location = ".".join(str(piece) for piece in item.get("loc", ()))
        parts.append(f"{location}: {item.get('msg')}" if location else str(item.get("msg")))
    return "; ".join(parts) or "invalid edit plan"


@router.post("/apply")
async def apply_edit(file: UploadFile = File(...), plan: str = Form(...)):
    edit_plan = parse_plan(plan)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    with workspace() as directory:
        with uploaded_file(directory, file.filename, content, "input.pdf") as source:
            result_file = output_path(directory, Path(file.filename or "input").stem, ".pdf")
            try:
                result = apply_edit_plan(str(source), str(result_file), edit_plan)
            except EditPlanError as error:
                raise HTTPException(status_code=400, detail=str(error))
            except (ValueError, TypeError) as error:
                raise HTTPException(status_code=422, detail=str(error))

            data = result_file.read_bytes()

    return Response(
        content=data,
        media_type=PDF_MEDIA_TYPE,
        headers={
            "Content-Disposition": f'attachment; filename="{result_file.name}"',
            "X-Docome-Operations": str(result.operation_count),
        },
    )


@router.get("/actions")
async def list_actions():
    return {"actions": EditPlanExecutor().available_actions()}
