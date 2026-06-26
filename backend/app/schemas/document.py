from pydantic import BaseModel
from typing import Optional
from enum import Enum

class DocumentType(str, Enum):
    EMAIL = "email"
    QUOTATION = "quotation"
    CONTRACT = "contract"
    MEETING_NOTES = "meeting_notes"

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    doc_type: DocumentType
    status: str
    message: str
