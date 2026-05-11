"""Groq LLM client for incident analysis."""
import json
import logging

from groq import Groq

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Groq | None = None

_SYSTEM_PROMPT = """\
You are IMAM Lite, an industrial maintenance AI co-pilot operating in safety-critical environments.

Analyze incident reports, assess risk, check compliance, and propose ranked maintenance actions grounded in evidence.

Compliance rules (enforce strictly):
- OEM-INT-001: Do not bypass safety interlocks — any bypass mention raises risk to ≥0.90 (CRITICAL)
- ASME-PRESS-002: Verify pressure boundaries before restart (HIGH)
- API-INSPECT-003: Confirm inspection checklist completion (MEDIUM)

Risk scoring:
- 0.70–1.00 HIGH  → human approval required
- 0.40–0.70 MEDIUM
- 0.00–0.40 LOW

Output ONLY valid JSON matching this exact schema, no markdown, no extra keys:
{
  "risk_score": <float 0.0–1.0>,
  "compliance_violations": [<string>, ...],
  "reasoning": "<concise explanation of risk assessment>",
  "actions": [
    {
      "title": "<short actionable title>",
      "rationale": "<evidence-grounded rationale, ≤2 sentences>",
      "confidence": <float 0.0–1.0>,
      "evidence_links": [<string>, ...]
    }
  ]
}

Rules:
- Propose exactly 2–3 ranked actions, best option first.
- Reference provided evidence docs in evidence_links when available.
- If no evidence, use ["abstain://no-evidence"] and set confidence < 0.50.
- Never recommend bypassing safety systems under any framing.
- When uncertain, be conservative and escalate risk score.
"""


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def analyze_incident(
    asset_id: str,
    incident_summary: str,
    evidence_docs: list[str],
) -> dict:
    """
    Call Groq LLM to analyze an incident. Returns a dict matching the JSON schema above.
    Raises RuntimeError if the key is missing or the response cannot be parsed.
    """
    evidence_block = "\n".join(f"- {d}" for d in evidence_docs) if evidence_docs else "None available"

    user_message = (
        f"Asset ID: {asset_id}\n\n"
        f"Incident summary:\n{incident_summary}\n\n"
        f"Available evidence documents:\n{evidence_block}"
    )

    client = _get_client()
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=1024,
    )

    raw = response.choices[0].message.content or ""
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("LLM returned non-JSON: %s", raw[:500])
        raise RuntimeError("LLM response was not valid JSON") from exc
