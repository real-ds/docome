import sys
from pathlib import Path

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "packages") not in sys.path:
    sys.path.insert(0, str(ROOT / "packages"))
if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.routes.conversion import router as conversion_router
from app.api.routes.editing import router as editing_router
from app.api.routes.pdf_ops import router as pdf_router

app = FastAPI(title="Docome API", version="0.1.0")

app.include_router(pdf_router)
app.include_router(conversion_router)
app.include_router(editing_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
