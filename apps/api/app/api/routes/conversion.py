from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.workspace import (
    DOCX_MEDIA_TYPE,
    PDF_MEDIA_TYPE,
    XLSX_MEDIA_TYPE,
    output_path,
    uploaded_file,
    workspace,
)
from conversion_engine import ConversionEngine, evaluate, pdf_to_docx_hq

router = APIRouter(prefix="/api/v1/convert", tags=["convert"])

MAX_UPLOAD_BYTES = 100 * 1024 * 1024

engine = ConversionEngine()


def attachment(data: bytes, filename: str, media_type: str, headers: Optional[Dict[str, str]] = None) -> Response:
    all_headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    if headers:
        all_headers.update(headers)
    return Response(content=data, media_type=media_type, headers=all_headers)


@router.post("/pdf2docx-hq")
async def convert_pdf2docx_hq(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded file is too large")

    stem = Path(file.filename or "document").stem
    with workspace() as directory:
        with uploaded_file(directory, file.filename, content, "input.pdf") as source:
            result_file = output_path(directory, stem, ".docx")
            try:
                pdf_to_docx_hq(str(source), str(result_file))
            except Exception as error:
                raise HTTPException(status_code=422, detail=str(error))
            data = result_file.read_bytes()

    return attachment(data, result_file.name, DOCX_MEDIA_TYPE)


@router.post("/fidelity")
async def conversion_fidelity(
    file: UploadFile = File(...),
    converted: UploadFile = File(...),
):
    source_content = await file.read()
    converted_content = await converted.read()
    if not source_content or not converted_content:
        raise HTTPException(status_code=400, detail="Both a source PDF and a converted file are required")

    with workspace() as directory:
        source = directory / "source.pdf"
        output = directory / "converted.docx"
        source.write_bytes(source_content)
        output.write_bytes(converted_content)

        try:
            report = evaluate(str(source), str(output))
        except Exception as error:
            raise HTTPException(status_code=422, detail=str(error))

    payload = report.as_dict()
    payload["failed_metrics"] = _failed_metrics(report)
    return payload


async def read_source(file: UploadFile):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded file is too large")
    return content


@router.post("/pdf2docx")
async def convert_pdf2docx(file: UploadFile = File(...)):
    content = await read_source(file)
    stem = Path(file.filename or "document").stem

    with workspace() as directory:
        with uploaded_file(directory, file.filename, content, "input.pdf") as source:
            result_file = output_path(directory, stem, ".docx")
            try:
                engine.pdf_to_docx(str(source), str(result_file))
            except Exception as error:
                raise HTTPException(status_code=422, detail=str(error))
            data = result_file.read_bytes()

    return attachment(data, result_file.name, DOCX_MEDIA_TYPE)


@router.post("/docx2pdf")
async def convert_docx2pdf(file: UploadFile = File(...)):
    content = await read_source(file)
    stem = Path(file.filename or "document").stem

    with workspace() as directory:
        with uploaded_file(directory, file.filename, content, "input.docx") as source:
            result_file = output_path(directory, stem, ".pdf")
            try:
                engine.docx_to_pdf(str(source), str(result_file))
            except Exception as error:
                raise HTTPException(status_code=422, detail=str(error))
            data = result_file.read_bytes()

    return attachment(data, result_file.name, PDF_MEDIA_TYPE)


@router.post("/pdf2xlsx")
async def convert_pdf2xlsx(file: UploadFile = File(...)):
    content = await read_source(file)
    stem = Path(file.filename or "document").stem

    with workspace() as directory:
        with uploaded_file(directory, file.filename, content, "input.pdf") as source:
            result_file = output_path(directory, stem, ".xlsx")
            try:
                engine.pdf_to_xlsx(str(source), str(result_file))
            except Exception as error:
                raise HTTPException(status_code=422, detail=str(error))
            data = result_file.read_bytes()

    return attachment(data, result_file.name, XLSX_MEDIA_TYPE)


@router.post("/pdf2txt")
async def convert_pdf2txt(file: UploadFile = File(...)):
    content = await read_source(file)
    try:
        return {"text": engine.pdf_to_text(content)}
    except Exception as error:
        raise HTTPException(status_code=422, detail=str(error))


@router.post("/pdf2md")
async def convert_pdf2md(file: UploadFile = File(...)):
    content = await read_source(file)
    try:
        return {"markdown": engine.pdf_to_markdown(content)}
    except Exception as error:
        raise HTTPException(status_code=422, detail=str(error))


def _failed_metrics(report) -> List[str]:
    failures = []
    if not report.page_count_preserved:
        failures.append("page_count")
    if report.text_retention < 0.9:
        failures.append("text_retention")
    if report.font_retention < 0.9:
        failures.append("font_retention")
    if not report.tables_preserved:
        failures.append("tables")
    if not report.images_preserved:
        failures.append("images")
    if not report.hyperlinks_preserved:
        failures.append("hyperlinks")
    return failures
