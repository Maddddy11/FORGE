from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.rbac import AuthenticatedUser, require_roles
from app.schemas.approvals import ApprovalRequest, ApprovalResponse
from app.schemas.common import AuditEvent
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
approval_service = ApprovalService()
audit_service = AuditService()


@router.post("/{recommendation_id}/approve", response_model=ApprovalResponse)
def approve_recommendation(
    recommendation_id: str,
    payload: ApprovalRequest,
    user: Annotated[AuthenticatedUser, Depends(require_roles("approver", "admin"))],
) -> ApprovalResponse:
    return approval_service.approve(recommendation_id, payload, actor=str(user.get("sub", "unknown")))


@router.get("/{recommendation_id}/audit", response_model=list[AuditEvent])
def get_audit(
    recommendation_id: str,
    user: Annotated[AuthenticatedUser, Depends(require_roles("approver", "admin"))],
) -> list[AuditEvent]:
    return audit_service.get_recommendation_audit(recommendation_id)
