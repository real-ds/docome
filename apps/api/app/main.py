import io
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "packages"))

from pdf_engine import PdfEngine, CompressLevel, Metadata, PageRange, Rotation
from conversion_engine import ConversionEngine

app = FastAPI(title="Docome API", version="0.1.0")

pdf_engine = PdfEngine()
conversion_engine = ConversionEngine()


class MetadataUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None


class PageOperation(BaseModel):
    pages: Optional[List[int]] = None
    start: Optional[int] = None
    end: Optional[int] = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/v1/pdf/merge")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    temp_paths = []
    try:
        for f in files:
            content = await f.read()
            temp_path = Path(f"/tmp/{f.filename}")
            temp_path.write_bytes(content)
            temp_paths.append(str(temp_path))

        output_path = f"/tmp/merged_{Path(files[0].filename).stem}.pdf"
        pdf_engine.merge(temp_paths, output_path)

        return FileResponse(output_path, media_type="application/pdf", filename="merged.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in temp_paths:
            Path(p).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


@app.post("/api/v1/pdf/split")
async def split_pdf(file: UploadFile = File(...), pages_per_split: int = 1):
    content = await file.read()
    temp_input = Path(f"/tmp/{file.filename}")
    temp_input.write_bytes(content)

    try:
        output_dir = f"/tmp/split_{Path(file.filename).stem}"
        pdf_engine.split(str(temp_input), output_dir, pages_per_split)

        files = list(Path(output_dir).glob("*.pdf"))
        return {"files": [f.name for f in files], "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        temp_input.unlink(missing_ok=True)


@app.post("/api/v1/pdf/extract")
async def extract_pages(
    file: UploadFile = File(...),
    pages: Optional[str] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
):
    content = await file.read()
    temp_input = Path(f"/tmp/{file.filename}")
    temp_input.write_bytes(content)

    try:
        output_path = f"/tmp/extracted_{Path(file.filename).stem}.pdf"

        page_range = None
        if start and end:
            page_range = PageRange(start=start, end=end)
        elif pages:
            page_list = [int(p) - 1 for p in pages.split(",")]
        else:
            page_list = None

        pdf_engine.extract(
            str(temp_input),
            output_path,
            pages=page_list if 'page_list' in dir() else None,
            page_range=page_range,
        )

        return FileResponse(output_path, media_type="application/pdf", filename="extracted.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        temp_input.unlink(missing_ok=True)


@app.post("/api/v1/pdf/rotate")
async def rotate_pdf(
    file: UploadFile = File(...),
    degrees: int = 90,
    pages: Optional[str] = None,
):
    content = await file.read()
    temp_input = Path(f"/tmp/{file.filename}")
    temp_input.write_bytes(content)

    try:
        output_path = f"/tmp/rotated_{Path(file.filename).stem}.pdf"

        rotation_map = {90: Rotation.ROTATE_90, 180: Rotation.ROTATE_180, 270: Rotation.ROTATE_270}
        if degrees not in rotation_map:
            raise HTTPException(status_code=400, detail="Invalid rotation degrees")

        page_list = None
        if pages:
            page_list = [int(p) - 1 for p in pages.split(",")]

        pdf_engine.rotate(str(temp_input), output_path, rotation_map[degrees], pages=page_list)

        return FileResponse(output_path, media_type="application/pdf", filename="rotated.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        temp_input.unlink(missing_ok=True)


@app.post("/api/v1/pdf/compress")
async def compress_pdf(
    file: UploadFile = File(...),
    level: str = "recommended",
):
    content = await file.read()
    temp_input = Path(f"/tmp/{file.filename}")
    temp_input.write_bytes(content)

    try:
        output_path = f"/tmp/compressed_{Path(file.filename).stem}.pdf"

        compress_level = CompressLevel(level)
        pdf_engine.compress(str(temp_input), output_path, compress_level)

        return FileResponse(output_path, media_type="application/pdf", filename="compressed.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        temp_input.unlink(missing_ok=True)


@app.get("/api/v1/pdf/metadata/{filename}")
async def get_metadata(filename: str):
    file_path = Path(f"/tmp/{filename}")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        meta = pdf_engine.get_metadata(str(file_path))
        return meta.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pdf/metadata/{filename}")
async def update_metadata(filename: str, metadata: MetadataUpdate):
    file_path = Path(f"/tmp/{filename}")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        output_path = f"/tmp/{filename}"
        meta = Metadata(**metadata.model_dump(exclude_none=True))
        pdf_engine.set_metadata(str(file_path), output_path, meta)

        return {"status": "updated", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pdf/pages")
async def get_page_count(file: UploadFile = File(...)):
    content = await file.read()
    temp_input = Path(f"/tmp/{file.filename}")
    temp_input.write_bytes(content)

    try:
        count = pdf_engine.get_page_count(str(temp_input))
        return {"page_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        temp_input.unlink(missing_ok=True)


@app.post("/api/v1/convert/pdf2docx")
async def convert_pdf2docx(file: UploadFile = File(...)):
    content = await file.read()
    temp_input = Path(f"/tmp/{file.filename}")
    temp_input.write_bytes(content)

    try:
        output_path = f"/tmp/{Path(file.filename).stem}.docx"
        conversion_engine.pdf_to_docx(str(temp_input), output_path)

        return FileResponse(output_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename="converted.docx")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        temp_input.unlink(missing_ok=True)


@app.post("/api/v1/convert/pdf2txt")
async def convert_pdf2txt(file: UploadFile = File(...)):
    content = await file.read()
    temp_input = Path(f"/tmp/{file.filename}")
    temp_input.write_bytes(content)

    try:
        text = conversion_engine.pdf_to_text(str(temp_input))
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        temp_input.unlink(missing_ok=True)


@app.post("/api/v1/convert/pdf2md")
async def convert_pdf2md(file: UploadFile = File(...)):
    content = await file.read()
    temp_input = Path(f"/tmp/{file.filename}")
    temp_input.write_bytes(content)

    try:
        md = conversion_engine.pdf_to_markdown(str(temp_input))
        return {"markdown": md}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        temp_input.unlink(missing_ok=True)


@app.post("/api/v1/convert/docx2pdf")
async def convert_docx2pdf(file: UploadFile = File(...)):
    content = await file.read()
    temp_input = Path(f"/tmp/{file.filename}")
    temp_input.write_bytes(content)

    try:
        output_path = f"/tmp/{Path(file.filename).stem}.pdf"
        conversion_engine.docx_to_pdf(str(temp_input), output_path)

        return FileResponse(output_path, media_type="application/pdf", filename="converted.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        temp_input.unlink(missing_ok=True)


@app.post("/api/v1/convert/pdf2xlsx")
async def convert_pdf2xlsx(file: UploadFile = File(...)):
    content = await file.read()
    temp_input = Path(f"/tmp/{file.filename}")
    temp_input.write_bytes(content)

    try:
        output_path = f"/tmp/{Path(file.filename).stem}.xlsx"
        conversion_engine.pdf_to_xlsx(str(temp_input), output_path)

        return FileResponse(output_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="converted.xlsx")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        temp_input.unlink(missing_ok=True)
