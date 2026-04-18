from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RecommendationState(str, Enum):
    draft = "draft"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"


class AuditEvent(BaseModel):
    event_id: str
    recommendation_id: str
    actor: str
    event_type: str
    timestamp: datetime
    details: dict = Field(default_factory=dict)
