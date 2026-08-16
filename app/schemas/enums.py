from enum import Enum


class SourceStatus(str, Enum):
    success = "success"
    failure = "failure"
    unknown = "unknown"


class SourceName(str, Enum):
    github = "github"
    github_actions = "github_actions"
    trivy = "trivy"
    terraform = "terraform"
    ecs = "ecs"
    cloudwatch = "cloudwatch"
    history = "history"
    synthetic = "synthetic"


class ScanStatus(str, Enum):
    clean = "clean"
    findings = "findings"
    scan_failed = "scan_failed"
    unavailable = "unavailable"


class EventType(str, Enum):
    CODE_CHANGE = "CODE_CHANGE"
    DEPLOYMENT = "DEPLOYMENT"
    DEPLOYMENT_FAILURE = "DEPLOYMENT_FAILURE"
    ROLLBACK = "ROLLBACK"
    INCIDENT_START = "INCIDENT_START"
    SERVICE_RESTORED = "SERVICE_RESTORED"


class AttributionMethod(str, Enum):
    explicit_release_id = "explicit_release_id"
    timestamp_correlation = "timestamp_correlation"
    synthetic = "synthetic"


class AttributionConfidence(str, Enum):
    attributed = "attributed"
    likely_related = "likely_related"
    unknown = "unknown"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Recommendation(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_HUMAN_REVIEW = "REQUIRE_HUMAN_REVIEW"
    BLOCK_APPROVAL_REQUIRED = "BLOCK_APPROVAL_REQUIRED"


class ApprovalState(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ApprovalDecision(str, Enum):
    approve = "approve"
    reject = "reject"


class SignalId(str, Enum):
    ci_failure = "ci_failure"
    critical_vulnerability = "critical_vulnerability"
    high_vulnerability = "high_vulnerability"
    database_migration = "database_migration"
    high_risk_infrastructure_change = "high_risk_infrastructure_change"
    rollback_required = "rollback_required"
    similar_historical_failure = "similar_historical_failure"
    large_change_surface = "large_change_surface"
    missing_critical_evidence = "missing_critical_evidence"


class DedupGroup(str, Enum):
    delivery_failure = "delivery_failure"
    security_critical = "security_critical"
    security_high = "security_high"
    schema_change = "schema_change"
    infra_change = "infra_change"
    historical_similarity = "historical_similarity"
    change_surface = "change_surface"
    evidence_completeness = "evidence_completeness"


class SignalSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
