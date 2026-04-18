from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.rbac import AuthenticatedUser, require_roles
from app.schemas.assets import AssetContextResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/assets", tags=["assets"])
service = RetrievalService()


@router.get("/{asset_id}/context", response_model=AssetContextResponse)
def get_asset_context(
    asset_id: str,
    user: Annotated[AuthenticatedUser, Depends(require_roles("operator", "approver", "admin"))],
) -> AssetContextResponse:
    return service.get_asset_context(asset_id)
