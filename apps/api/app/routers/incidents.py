from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.rbac import AuthenticatedUser, require_roles
from app.schemas.incidents import IncidentAnalyzeRequest, IncidentAnalyzeResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/incidents", tags=["incidents"])
service = RecommendationService()


@router.post("/analyze", response_model=IncidentAnalyzeResponse)
def analyze_incident(
    payload: IncidentAnalyzeRequest,
    user: Annotated[AuthenticatedUser, Depends(require_roles("operator", "admin"))],
) -> IncidentAnalyzeResponse:
    return service.analyze(payload, actor=str(user.get("sub", "unknown")))
