import httpx

from app.config import Settings
from app.schemas.assessment import AiExplanation, Assessment
from app.schemas.enums import SourceStatus
from app.schemas.evidence import ReleaseEvidence

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

_SYSTEM_PROMPT = """You explain a ReleaseGuard release-risk assessment to a human approver.
Use only the facts in the user message.
Do not invent CI results, vulnerability counts, DORA metrics, incidents, or timestamps.
If a source is unknown or missing, say it is unknown.
Do not change or dispute the risk_score, signals, or recommendation.
DORA numbers are delivery performance, not the risk score.
Keep the explanation to a few short paragraphs."""


def _facts(assessment: Assessment, evidence: ReleaseEvidence) -> dict:
    return {
        "release_id": assessment.release_id,
        "risk_score": assessment.risk_score,
        "risk_level": assessment.risk_level.value,
        "recommendation": assessment.recommendation.value,
        "enforcement": assessment.enforcement,
        "signals": [
            {
                "signal": item.signal.value,
                "weight": item.weight,
                "evidence": item.evidence,
                "source": item.source.value,
            }
            for item in assessment.signals
        ],
        "evidence_summary": assessment.evidence_summary.model_dump(mode="json"),
        "missing_sources": evidence.missing_sources,
        "failed_sources": evidence.failed_sources,
        "is_synthetic": evidence.is_synthetic,
        "history": evidence.history.model_dump(mode="json"),
        "dora_context": assessment.dora_context.model_dump(mode="json"),
    }


def groq_chat(api_key: str, payload: dict) -> tuple[int, dict | None]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=20.0) as client:
        response = client.post(GROQ_URL, headers=headers, json=payload)
        if response.status_code >= 400:
            return response.status_code, None
        return response.status_code, response.json()


def explain_assessment(
    assessment: Assessment,
    evidence: ReleaseEvidence,
    settings: Settings,
    http_post=None,
) -> Assessment:
    if not settings.groq_api_key:
        assessment.ai_explanation = AiExplanation(status=SourceStatus.unknown)
        return assessment

    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.2,
        "max_tokens": 400,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": str(_facts(assessment, evidence))},
        ],
    }

    def do_post() -> tuple[int, dict | None]:
        if http_post is not None:
            return http_post(GROQ_URL, payload)
        return groq_chat(settings.groq_api_key, payload)

    status, body = do_post()
    text = None
    if isinstance(body, dict):
        choices = body.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content")
            if content:
                text = str(content).strip()

    if status >= 400 or not text:
        assessment.ai_explanation = AiExplanation(status=SourceStatus.failure)
        return assessment

    assessment.ai_explanation = AiExplanation(status=SourceStatus.success, text=text)
    return assessment
