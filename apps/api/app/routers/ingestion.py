from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.rbac import AuthenticatedUser, require_roles
from app.schemas.ingestion import IngestRequest, IngestResponse
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])
service = IngestionService()


@router.post("/documents", response_model=IngestResponse)
def ingest_documents(
    payload: IngestRequest,
    user: Annotated[AuthenticatedUser, Depends(require_roles("operator", "admin"))],
) -> IngestResponse:
    return service.ingest(payload)
