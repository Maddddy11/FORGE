from fastapi import APIRouter, HTTPException, status
from typing import Annotated
from fastapi import Depends

from app.core.rbac import AuthenticatedUser, require_roles
from app.services import db_service, ml_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/asset-health")
def asset_health(
    user: Annotated[AuthenticatedUser, Depends(require_roles("operator", "approver", "admin"))],
) -> dict:
    try:
        data = db_service.get_asset_health()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return {
        "assets": data,
        "ml_models_active": ml_service.models_available(),
    }


@router.get("/kpis")
def incident_kpis(
    user: Annotated[AuthenticatedUser, Depends(require_roles("operator", "approver", "admin"))],
) -> dict:
    try:
        data = db_service.get_incident_kpis()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    total_incidents = sum(r["incident_count"] for r in data)
    total_high_risk = sum(r["high_risk_count"] for r in data)
    avg_mttd = (
        sum(r["avg_mttd_high_risk_hrs"] or 0 for r in data) / len(data)
        if data else None
    )

    return {
        "summary": {
            "total_incidents":       total_incidents,
            "total_high_risk":       total_high_risk,
            "high_risk_rate":        round(total_high_risk / max(total_incidents, 1), 3),
            "avg_mttd_high_risk_hrs": round(avg_mttd, 2) if avg_mttd else None,
        },
        "daily": data,
    }
