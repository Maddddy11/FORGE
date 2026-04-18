from uuid import uuid4

from app.schemas.ingestion import IngestRequest, IngestResponse
from app.services.store import store


class IngestionService:
    def ingest(self, request: IngestRequest) -> IngestResponse:
        ingestion_id = str(uuid4())
        warnings: list[str] = []

        for doc in request.documents:
            extracted_metadata = {
                "asset_id": doc.asset_id,
                "doc_type": doc.doc_type,
                "filename": doc.filename,
                "content_preview": doc.content[:160],
            }
            store.documents.append(extracted_metadata)

            if len(doc.content.strip()) < 30:
                warnings.append(f"Document '{doc.filename}' is short; verify OCR quality.")

        return IngestResponse(
            ingestion_id=ingestion_id,
            stored_documents=len(request.documents),
            warnings=warnings,
        )
