"""LangGraph orchestration placeholder for MVP graph state machine."""


def flow_definition() -> list[str]:
    return [
        "classify_intent",
        "retrieve_context",
        "generate_actions",
        "compliance_check",
        "risk_gate",
        "finalize_response",
        "write_audit_log",
    ]
