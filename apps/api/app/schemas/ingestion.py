from pydantic import BaseModel, Field


class DocumentIn(BaseModel):
    filename: str = Field(min_length=1, max_length=256)
    asset_id: str = Field(min_length=1, max_length=128)
    doc_type: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1)


class IngestRequest(BaseModel):
    documents: list[DocumentIn] = Field(min_length=1)


class IngestResponse(BaseModel):
    ingestion_id: str
    stored_documents: int
    warnings: list[str] = Field(default_factory=list)
