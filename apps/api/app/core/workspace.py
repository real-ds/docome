import re
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Union

SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PDF_MEDIA_TYPE = "application/pdf"


def safe_name(filename: Optional[str], fallback: str = "upload") -> str:
    if not filename:
        return fallback
    stem = Path(filename).name
    cleaned = SAFE_NAME.sub("_", stem).strip("._-")
    return cleaned or fallback


@contextmanager
def workspace(prefix: str = "docome-") -> Iterator[Path]:
    directory = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield directory
    finally:
        shutil.rmtree(directory, ignore_errors=True)


INPUT_DIR = "_in"


def input_dir(directory: Path) -> Path:
    path = directory / INPUT_DIR
    path.mkdir(exist_ok=True)
    return path


def write_upload(directory: Path, filename: Optional[str], content: bytes, fallback: str = "upload") -> Path:
    target = input_dir(directory) / safe_name(filename, fallback)
    target.write_bytes(content)
    return target


@contextmanager
def uploaded_file(
    directory: Path,
    filename: Optional[str],
    content: bytes,
    fallback: str = "upload",
) -> Iterator[Path]:
    path = write_upload(directory, filename, content, fallback)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def output_path(directory: Path, stem: str, suffix: str) -> Path:
    return directory / f"{safe_name(stem, 'output')}{suffix}"
