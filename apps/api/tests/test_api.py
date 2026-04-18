from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def _token(role: str, sub: str = "tester") -> str:
    now = datetime.now(tz=UTC)
    payload = {
        "sub": sub,
        "role": role,
        "aud": settings.jwt_audience,
        "iss": settings.jwt_issuer,
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _auth(role: str) -> dict:
    return {"Authorization": f"Bearer {_token(role)}"}


def test_health_open():
    response = client.get("/health")
    assert response.status_code == 200


def test_ingest_and_context_flow():
    ingest_payload = {
        "documents": [
            {
                "filename": "pump_manual.pdf",
                "asset_id": "P-100",
                "doc_type": "oem_manual",
                "content": "Pump startup checklist and seal inspection schedule.",
            }
        ]
    }

    ingest = client.post("/ingest/documents", headers=_auth("operator"), json=ingest_payload)
    assert ingest.status_code == 200
    assert ingest.json()["stored_documents"] == 1

    context = client.get("/assets/P-100/context", headers=_auth("operator"))
    assert context.status_code == 200
    assert len(context.json()["linked_documents"]) >= 1


def test_approval_requires_approver_role():
    analyze = client.post(
        "/incidents/analyze",
        headers=_auth("operator"),
        json={"asset_id": "A-10", "incident_summary": "Fire alarm near compressor, possible leak."},
    )
    assert analyze.status_code == 200
    recommendation_id = analyze.json()["recommendation_id"]

    denied = client.post(
        f"/recommendations/{recommendation_id}/approve",
        headers=_auth("operator"),
        json={"approved": True, "reason": "Not allowed role"},
    )
    assert denied.status_code == 403

    allowed = client.post(
        f"/recommendations/{recommendation_id}/approve",
        headers=_auth("approver"),
        json={"approved": True, "reason": "Reviewed by supervisor"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["state"] == "approved"
