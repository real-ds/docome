from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class CompressLevel(str, Enum):
    EXTREME = "extreme"
    HIGH = "high"
    RECOMMENDED = "recommended"
    LOW = "low"


class Rotation(str, Enum):
    ROTATE_90 = "90"
    ROTATE_180 = "180"
    ROTATE_270 = "270"


class PageRange(BaseModel):
    start: int = Field(ge=1, description="Start page (1-indexed)")
    end: Optional[int] = Field(default=None, ge=1, description="End page (inclusive)")

    def to_pages(self, total_pages: int) -> list[int]:
        end = self.end or total_pages
        return list(range(self.start - 1, min(end, total_pages)))


class Metadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    keywords: Optional[str] = None
    creation_date: Optional[str] = None
    mod_date: Optional[str] = None


class PdfOperation(str, Enum):
    MERGE = "merge"
    SPLIT = "split"
    EXTRACT = "extract"
    REMOVE = "remove"
    REORDER = "reorder"
    ROTATE = "rotate"
    COMPRESS = "compress"
    METADATA = "metadata"
    PROTECT = "protect"
    VALIDATE = "validate"
