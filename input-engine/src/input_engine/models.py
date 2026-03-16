from datetime import datetime

from pydantic import BaseModel, Field


class ExtractionOptions(BaseModel):
    include_metadata: bool = True
    include_media_refs: bool = True


class ExtractionRequest(BaseModel):
    content: str
    content_type: str | None = None
    options: ExtractionOptions = Field(default_factory=ExtractionOptions)


class MediaRef(BaseModel):
    type: str
    url: str
    description: str | None = None
    timestamp: str | None = None


class ExtractionResult(BaseModel):
    source_type: str
    source_url: str | None = None
    title: str | None = None
    content: str
    metadata: dict = Field(default_factory=dict)
    media: list[MediaRef] = Field(default_factory=list)
    extracted_at: datetime
    extraction_method: str
    confidence: float = 1.0


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    source_type: str | None = None
