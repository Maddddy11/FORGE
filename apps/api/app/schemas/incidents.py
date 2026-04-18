from pydantic import BaseModel, Field

from app.schemas.common import RecommendationState


class IncidentAnalyzeRequest(BaseModel):
    asset_id: str = Field(min_length=1, max_length=128)
    incident_summary: str = Field(min_length=5, max_length=5000)


class ActionOption(BaseModel):
    title: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_links: list[str]


class IncidentAnalyzeResponse(BaseModel):
    recommendation_id: str
    asset_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    compliance_violations: list[str]
    actions: list[ActionOption]
    state: RecommendationState
