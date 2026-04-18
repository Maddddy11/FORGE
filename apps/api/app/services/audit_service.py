from app.schemas.common import AuditEvent
from app.services.store import store


class AuditService:
    def get_recommendation_audit(self, recommendation_id: str) -> list[AuditEvent]:
        return [event for event in store.audits if event.recommendation_id == recommendation_id]
