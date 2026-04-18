from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.common import AuditEvent, RecommendationState


@dataclass
class MemoryStore:
    documents: list[dict] = field(default_factory=list)
    recommendations: dict = field(default_factory=dict)
    audits: list[AuditEvent] = field(default_factory=list)

    def append_audit(self, recommendation_id: str, actor: str, event_type: str, details: dict) -> AuditEvent:
        event = AuditEvent(
            event_id=str(uuid4()),
            recommendation_id=recommendation_id,
            actor=actor,
            event_type=event_type,
            timestamp=datetime.now(tz=UTC),
            details=details,
        )
        self.audits.append(event)
        return event


store = MemoryStore()


def approval_state_from_bool(approved: bool) -> RecommendationState:
    return RecommendationState.approved if approved else RecommendationState.rejected
