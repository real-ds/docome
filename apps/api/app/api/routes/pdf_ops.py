import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError

from app.core.workspace import (
    PDF_MEDIA_TYPE,
    input_dir,
    safe_name,
    uploaded_file,
    workspace,
)
from pdf_engine import CompressLevel, Metadata, PageRange, PdfEngine, Rotation

router = APIRouter(prefix="/api/v1/pdf", tags=["pdf"])

engine = PdfEngine()

ROTATIONS = {
    90: Rotation.ROTATE_90,
    180: Rotation.ROTATE_180,
    270: Rotation.ROTATE_270,
}

COMPRESSION_LEVELS = {level.value.lower(): level for level in CompressLevel}


class MetadataUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None


def pdf_response(data: bytes, filename: str) -> Response:
    return Response(
        content=data,
        media_type=PDF_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def parse_pages(pages: Optional[str]) -> Optional[List[int]]:
    if not pages:
        return None
    try:
        return [int(part) - 1 for part in pages.split(",") if part.strip()]
    except ValueError as error:
        raise HTTPException(status_code=400, detail="pages must be comma-separated page numbers") from error


def parse_range(start: Optional[int], end: Optional[int]) -> Optional[PageRange]:
    if start is None or end is None:
        return None
    if start < 1 or end < start:
        raise HTTPException(status_code=400, detail="invalid page range")
    return PageRange(start=start, end=end)


async def read_upload(file: UploadFile) -> bytes:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    return content


@router.post("/merge")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least two files are required")

    with workspace() as directory:
        uploads = input_dir(directory)
        sources = []
        for index, upload in enumerate(files):
            content = await read_upload(upload)
            path = uploads / f"part-{index}-{safe_name(upload.filename, 'file.pdf')}"
            path.write_bytes(content)
            sources.append(path)

        result_file = directory / "merged.pdf"
        try:
            engine.merge([str(path) for path in sources], str(result_file))
            data = result_file.read_bytes()
        except Exception as error:
            raise HTTPException(status_code=422, detail=str(error))

    return pdf_response(data, "merged.pdf")


@router.post("/split")
async def split_pdf(file: UploadFile = File(...), pages_per_split: int = Form(1)):
    if pages_per_split < 1:
        raise HTTPException(status_code=400, detail="pages_per_split must be at least 1")

    content = await read_upload(file)
    with workspace() as directory:
        with uploaded_file(directory, file.filename, content, "input.pdf") as source:
            out_dir = directory / "split"
            try:
                produced = engine.split(str(source), str(out_dir), pages_per_split)
            except Exception as error:
                raise HTTPException(status_code=422, detail=str(error))
            parts = {path.name: path.read_bytes() for path in produced if path.exists()}

    if not parts:
        raise HTTPException(status_code=422, detail="split produced no files")

    if len(parts) == 1:
        return pdf_response(next(iter(parts.values())), "split.pdf")

    buffer = _zip(parts)
    return Response(
        content=buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="split.zip"'},
    )


def _zip(parts: Dict[str, bytes]) -> bytes:
    import io

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            archive.writestr(name, payload)
    return buffer.getvalue()


@router.post("/extract")
async def extract_pages(
    file: UploadFile = File(...),
    pages: Optional[str] = Form(None),
    start: Optional[int] = Form(None),
    end: Optional[int] = Form(None),
):
    content = await read_upload(file)
    page_list = parse_pages(pages)
    page_range = parse_range(start, end)

    if page_list is None and page_range is None:
        raise HTTPException(status_code=400, detail="Provide pages or a start/end range")

    with workspace() as directory:
        with uploaded_file(directory, file.filename, content, "input.pdf") as source:
            result_file = directory / "extracted.pdf"
            try:
                engine.extract(str(source), str(result_file), pages=page_list, page_range=page_range)
            except Exception as error:
                raise HTTPException(status_code=422, detail=str(error))
            data = result_file.read_bytes()

    return pdf_response(data, "extracted.pdf")


@router.post("/rotate")
async def rotate_pdf(file: UploadFile = File(...), degrees: int = Form(90), pages: Optional[str] = Form(None)):
    if degrees not in ROTATIONS:
        raise HTTPException(status_code=400, detail="degrees must be 90, 180, or 270")

    content = await read_upload(file)
    with workspace() as directory:
        with uploaded_file(directory, file.filename, content, "input.pdf") as source:
            result_file = directory / "rotated.pdf"
            try:
                engine.rotate(str(source), str(result_file), ROTATIONS[degrees], pages=parse_pages(pages))
            except Exception as error:
                raise HTTPException(status_code=422, detail=str(error))
            data = result_file.read_bytes()

    return pdf_response(data, "rotated.pdf")


@router.post("/compress")
async def compress_pdf(file: UploadFile = File(...), level: str = Form("recommended")):
    resolved = COMPRESSION_LEVELS.get(str(level).lower())
    if resolved is None:
        allowed = ", ".join(sorted(COMPRESSION_LEVELS))
        raise HTTPException(status_code=400, detail=f"level must be one of: {allowed}")

    content = await read_upload(file)
    with workspace() as directory:
        with uploaded_file(directory, file.filename, content, "input.pdf") as source:
            result_file = directory / "compressed.pdf"
            try:
                engine.compress(str(source), str(result_file), resolved)
            except Exception as error:
                raise HTTPException(status_code=422, detail=str(error))
            data = result_file.read_bytes()

    return pdf_response(data, "compressed.pdf")


@router.post("/metadata/read")
async def get_metadata(file: UploadFile = File(...)):
    content = await read_upload(file)
    try:
        meta = engine.get_metadata(content)
    except Exception as error:
        raise HTTPException(status_code=422, detail=str(error))
    return meta.model_dump()


@router.post("/metadata")
async def update_metadata(file: UploadFile = File(...), metadata: str = Form(...)):
    try:
        payload = MetadataUpdate.model_validate_json(metadata)
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    content = await read_upload(file)
    with workspace() as directory:
        with uploaded_file(directory, file.filename, content, "input.pdf") as source:
            result_file = directory / "metadata.pdf"
            try:
                engine.set_metadata(
                    str(source), str(result_file),
                    Metadata(**payload.model_dump(exclude_none=True)),
                )
            except Exception as error:
                raise HTTPException(status_code=422, detail=str(error))
            data = result_file.read_bytes()

    return pdf_response(data, "metadata.pdf")


@router.post("/pages/count")
async def page_count(file: UploadFile = File(...)):
    content = await read_upload(file)
    try:
        return {"page_count": engine.get_page_count(content)}
    except Exception as error:
        raise HTTPException(status_code=422, detail=str(error))
