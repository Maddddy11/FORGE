import logging
from uuid import uuid4

from app.schemas.common import RecommendationState
from app.schemas.incidents import ActionOption, IncidentAnalyzeRequest, IncidentAnalyzeResponse
from app.services import llm_service, ml_service
from app.services.store import store

logger = logging.getLogger(__name__)

# Hard-coded safety overrides — LLM risk score is floored to these when matched.
_CRITICAL_KEYWORDS = {"bypass", "interlock"}
_HIGH_RISK_KEYWORDS = {"fire", "rupture", "leak", "trip", "shutdown"}


def _keyword_risk_floor(text: str) -> float:
    lower = text.lower()
    if any(k in lower for k in _CRITICAL_KEYWORDS):
        return 0.90
    if any(k in lower for k in _HIGH_RISK_KEYWORDS):
        return 0.70
    return 0.0


def _fallback_response(request: IncidentAnalyzeRequest) -> dict:
    """Rule-based fallback used when the LLM is unavailable."""
    risk_floor = _keyword_risk_floor(request.incident_summary)
    risk_score = max(risk_floor, 0.35)
    violations = []
    if "bypass" in request.incident_summary.lower():
        violations.append("OEM-INT-001: Potential bypass of safety interlock")
    return {
        "risk_score": risk_score,
        "compliance_violations": violations,
        "reasoning": "LLM unavailable — keyword-based fallback used.",
        "actions": [
            {
                "title": "Perform controlled inspection and verify instrumentation",
                "rationale": "Evidence-grounded first response minimising unintended downtime risk.",
                "confidence": 0.40,
                "evidence_links": ["abstain://no-evidence"],
            },
            {
                "title": "Escalate to maintenance planner with OEM checklist",
                "rationale": "Coordinated, standards-aligned execution.",
                "confidence": 0.35,
                "evidence_links": ["abstain://no-evidence"],
            },
        ],
    }


class RecommendationService:
    def analyze(self, request: IncidentAnalyzeRequest, actor: str) -> IncidentAnalyzeResponse:
        recommendation_id = str(uuid4())
        linked_docs = [doc for doc in store.documents if doc.get("asset_id") == request.asset_id]
        evidence_docs = [f"doc://{doc['filename']}" for doc in linked_docs[:5]]

        try:
            result = llm_service.analyze_incident(
                asset_id=request.asset_id,
                incident_summary=request.incident_summary,
                evidence_docs=evidence_docs,
            )
        except Exception:
            logger.warning("LLM call failed, falling back to rule-based analysis", exc_info=True)
            result = _fallback_response(request)

        # Safety overrides: highest of LLM score, keyword floor, and ML classifier wins.
        risk_floor = _keyword_risk_floor(request.incident_summary)
        ml_risk    = ml_service.classify_risk(request.incident_summary)
        risk_score = float(max(
            result.get("risk_score", 0.35),
            risk_floor,
            ml_risk or 0.0,
        ))
        risk_score = min(risk_score, 1.0)

        compliance_violations: list[str] = result.get("compliance_violations", [])

        actions = [
            ActionOption(
                title=a.get("title", "Unnamed action"),
                rationale=a.get("rationale", ""),
                confidence=float(min(max(a.get("confidence", 0.5), 0.0), 1.0)),
                evidence_links=a.get("evidence_links", ["abstain://no-evidence"]),
            )
            for a in result.get("actions", [])
        ]

        state = RecommendationState.pending_approval if risk_score >= 0.70 else RecommendationState.draft

        response = IncidentAnalyzeResponse(
            recommendation_id=recommendation_id,
            asset_id=request.asset_id,
            risk_score=risk_score,
            compliance_violations=compliance_violations,
            actions=actions,
            state=state,
        )

        store.recommendations[recommendation_id] = response.model_dump()
        store.append_audit(
            recommendation_id,
            actor=actor,
            event_type="recommendation_generated",
            details={**response.model_dump(), "reasoning": result.get("reasoning", "")},
        )

        return response
