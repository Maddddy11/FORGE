from uuid import uuid4

from app.schemas.common import RecommendationState
from app.schemas.incidents import ActionOption, IncidentAnalyzeRequest, IncidentAnalyzeResponse
from app.services.store import store


class RecommendationService:
    def analyze(self, request: IncidentAnalyzeRequest, actor: str) -> IncidentAnalyzeResponse:
        recommendation_id = str(uuid4())
        linked_docs = [doc for doc in store.documents if doc.get("asset_id") == request.asset_id]

        evidence = [f"doc://{doc['filename']}" for doc in linked_docs[:3]]
        if not evidence:
            evidence = ["abstain://no-evidence"]

        high_risk_keywords = ("fire", "rupture", "leak", "trip", "shutdown")
        risk_score = 0.8 if any(k in request.incident_summary.lower() for k in high_risk_keywords) else 0.35

        compliance_violations = []
        if "bypass" in request.incident_summary.lower():
            compliance_violations.append("Potential bypass of OEM safety interlock")
            risk_score = max(risk_score, 0.9)

        state = RecommendationState.pending_approval if risk_score >= 0.7 else RecommendationState.draft

        response = IncidentAnalyzeResponse(
            recommendation_id=recommendation_id,
            asset_id=request.asset_id,
            risk_score=risk_score,
            compliance_violations=compliance_violations,
            actions=[
                ActionOption(
                    title="Perform controlled inspection and verify instrumentation",
                    rationale="Evidence-grounded first response minimizing unintended downtime risk.",
                    confidence=0.82 if evidence[0] != "abstain://no-evidence" else 0.4,
                    evidence_links=evidence,
                ),
                ActionOption(
                    title="Escalate to maintenance planner with OEM checklist",
                    rationale="Escalation for coordinated, standards-aligned execution.",
                    confidence=0.78 if evidence[0] != "abstain://no-evidence" else 0.45,
                    evidence_links=evidence,
                ),
            ],
            state=state,
        )

        store.recommendations[recommendation_id] = response.model_dump()
        store.append_audit(recommendation_id, actor=actor, event_type="recommendation_generated", details=response.model_dump())

        return response
