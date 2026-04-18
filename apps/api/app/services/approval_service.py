from fastapi import HTTPException, status

from app.schemas.approvals import ApprovalRequest, ApprovalResponse
from app.schemas.common import RecommendationState
from app.services.store import approval_state_from_bool, store


class ApprovalService:
    def approve(self, recommendation_id: str, request: ApprovalRequest, actor: str) -> ApprovalResponse:
        recommendation = store.recommendations.get(recommendation_id)
        if recommendation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

        current_state = recommendation.get("state")
        if current_state not in {RecommendationState.pending_approval, RecommendationState.draft}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Recommendation already finalized")

        next_state = approval_state_from_bool(request.approved)
        recommendation["state"] = next_state
        store.recommendations[recommendation_id] = recommendation

        store.append_audit(
            recommendation_id,
            actor=actor,
            event_type="recommendation_approved" if request.approved else "recommendation_rejected",
            details={"reason": request.reason},
        )

        return ApprovalResponse(recommendation_id=recommendation_id, state=next_state)
