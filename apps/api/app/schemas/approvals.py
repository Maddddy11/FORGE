from pydantic import BaseModel

from app.schemas.common import RecommendationState


class ApprovalRequest(BaseModel):
    approved: bool
    reason: str


class ApprovalResponse(BaseModel):
    recommendation_id: str
    state: RecommendationState
