from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SignatureType(str, Enum):
    DRAW = "draw"
    TYPE = "type"
    UPLOAD = "upload"


class SignaturePosition(BaseModel):
    page: int = Field(ge=1, description="Page number (1-indexed)")
    x: float = Field(ge=0, description="X coordinate")
    y: float = Field(ge=0, description="Y coordinate")
    width: Optional[float] = Field(default=None, ge=0, description="Signature width")
    height: Optional[float] = Field(default=None, ge=0, description="Signature height")


class SignatureField(BaseModel):
    id: str
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None
    signature_type: SignatureType
    position: SignaturePosition
    filled: bool = False
    signature_data: Optional[str] = None


class SignatureRequest(BaseModel):
    id: str
    document_path: str
    signers: list[dict]
    status: str = "pending"
    created_at: Optional[str] = None
