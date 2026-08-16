from app.ai.explain import explain_assessment
from app.config import Settings
from app.normalize import expand_release_evidence
from app.risk.engine import assess
from app.schemas.enums import SourceStatus
from app.schemas.evidence import ReleaseEvidenceSubmit


def _assessment():
    submit = ReleaseEvidenceSubmit(
        release_id="REL-ai",
        repository="releaseguard-ai",
        commit_sha="abc123def456",
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
        critical_vulnerabilities=0,
        high_vulnerabilities=2,
    )
    evidence = expand_release_evidence(submit)
    return evidence, assess(evidence)


def test_missing_groq_key_leaves_explanation_unknown() -> None:
    evidence, assessment = _assessment()
    score = assessment.risk_score
    explained = explain_assessment(assessment, evidence, Settings(groq_api_key=None))
    assert explained.risk_score == score
    assert explained.ai_explanation.status == SourceStatus.unknown
    assert explained.ai_explanation.text is None


def test_groq_text_does_not_change_score() -> None:
    evidence, assessment = _assessment()
    score = assessment.risk_score

    def fake_post(_url: str, _payload: dict):
        return 200, {
            "choices": [
                {
                    "message": {
                        "content": "High vulnerabilities added 15 to the score. GitHub details are unknown."
                    }
                }
            ]
        }

    explained = explain_assessment(
        assessment,
        evidence,
        Settings(groq_api_key="test-key"),
        http_post=fake_post,
    )
    assert explained.risk_score == score
    assert explained.recommendation == assessment.recommendation
    assert explained.ai_explanation.status == SourceStatus.success
    assert "High vulnerabilities" in explained.ai_explanation.text


def test_failed_groq_call_is_failure_not_invented() -> None:
    evidence, assessment = _assessment()
    score = assessment.risk_score

    def fake_post(_url: str, _payload: dict):
        return 401, None

    explained = explain_assessment(
        assessment,
        evidence,
        Settings(groq_api_key="bad-key"),
        http_post=fake_post,
    )
    assert explained.risk_score == score
    assert explained.ai_explanation.status == SourceStatus.failure
    assert explained.ai_explanation.text is None
