"""Shared fixtures. Mocks the Groq LLM so CI never makes real API calls."""
import pytest


_LLM_RESPONSE = {
    "risk_score": 0.8,
    "compliance_violations": [],
    "reasoning": "Test mock — controlled inspection warranted given reported symptoms.",
    "actions": [
        {
            "title": "Perform controlled inspection and verify instrumentation",
            "rationale": "Evidence-grounded first response minimising unintended downtime risk.",
            "confidence": 0.85,
            "evidence_links": ["abstain://no-evidence"],
        },
        {
            "title": "Escalate to maintenance planner with OEM checklist",
            "rationale": "Coordinated, standards-aligned execution.",
            "confidence": 0.75,
            "evidence_links": ["abstain://no-evidence"],
        },
    ],
}


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm_service.analyze_incident",
        lambda asset_id, incident_summary, evidence_docs: _LLM_RESPONSE,
    )
