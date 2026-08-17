# ReleaseGuard AI — Release Evidence and DORA Event Contracts

**Status:** Accepted for MVP  
**Task:** RG-002  
**Date:** 2026-08-16

This file is the implementation source of truth for normalized release evidence, risk signals, and DORA events.

Do not invent extra fields at implementation time. If a source cannot fill a required field, mark the source `unknown` / `unavailable` instead of guessing.

All timestamps are ISO-8601 UTC.

---

## 1. First vertical slice

First complete evidence flow:

```text
GitHub
  → GitHub Actions (build + test)
  → Trivy
  → ReleaseGuard
  → Risk assessment
```

First-slice sources:
- GitHub: commits, PRs, changed files, authors, timestamps
- GitHub Actions: build status, test status, workflow duration, deployment workflow
- Trivy: CRITICAL / HIGH / MEDIUM / LOW findings

AWS/ECS is **not** required to prove the risk engine. ECS evidence is a later slice.

First UI is `/dashboard` only. Other App Router routes are planned, not current work.

---

## 2. Status and unknown-data rules

Use these enums everywhere status is recorded:

| Value | Meaning |
|---|---|
| `success` | Source ran and reported success / clean-enough result |
| `failure` | Source ran and reported failure |
| `unknown` | Source missing, timed out, not configured, or result cannot be trusted |

Rules:
- `failure` and `unknown` must never be stored or displayed as `success`.
- A missing source is `unknown`, not zero risk and not a clean scan.
- A Trivy scanner crash is `scan_failed`, which is not a clean scan.
- Synthetic records must set `is_synthetic: true` and must never be presented as real enterprise history.

---

## 3. Release identity

| Field | Required | Notes |
|---|---|---|
| `release_id` | yes | Stable id, e.g. `REL-001` |
| `repository` | yes | Configured GitHub repo, e.g. `releaseguard-ai` |
| `commit_sha` | yes | Git SHA being released |
| `service` | no | Defaults to repository name if omitted |
| `environment` | no | Default `production` when assessing a production release |
| `created_at` | yes | When this evidence bundle was assembled |

One configured GitHub repository for MVP. The adapter must accept `repository` so additional repos can be added later without changing this contract.

---

## 4. Normalized release evidence

This is the object ReleaseGuard persists and scores.

### 4.1 Compact first-slice input

Valid minimal payload for the first engine:

```json
{
  "release_id": "REL-001",
  "repository": "releaseguard-ai",
  "commit_sha": "abc123def456",
  "ci_status": "success",
  "test_status": "success",
  "critical_vulnerabilities": 0,
  "high_vulnerabilities": 2
}
```

Compact fields are a convenience view. The canonical stored object is `ReleaseEvidence` below. Adapters must expand compact input into `ReleaseEvidence` and keep source/unknown metadata.

### 4.2 Canonical `ReleaseEvidence`

```json
{
  "release_id": "REL-001",
  "repository": "releaseguard-ai",
  "commit_sha": "abc123def456",
  "service": "releaseguard-ai",
  "environment": "production",
  "created_at": "2026-08-16T17:30:00Z",
  "github": {
    "status": "success",
    "source": "github",
    "pull_request_number": 42,
    "first_commit_sha": "aaa111",
    "first_commit_at": "2026-08-16T09:00:00Z",
    "head_commit_sha": "abc123def456",
    "head_commit_at": "2026-08-16T16:00:00Z",
    "authors": ["dev-a"],
    "changed_files_count": 28,
    "lines_changed": 640,
    "changed_files": [
      {"path": "app/main.py", "change_type": "modified"},
      {"path": "alembic/versions/20260816_add_approvals.py", "change_type": "added"}
    ],
    "database_migration_detected": true
  },
  "github_actions": {
    "status": "success",
    "source": "github_actions",
    "ci_status": "success",
    "test_status": "success",
    "workflow_name": "ci",
    "workflow_run_id": "123456789",
    "workflow_duration_seconds": 180,
    "deployment_workflow_status": "unknown"
  },
  "trivy": {
    "status": "success",
    "source": "trivy",
    "scan_status": "findings",
    "critical": 0,
    "high": 2,
    "medium": 4,
    "low": 11,
    "findings": [
      {
        "vulnerability_id": "CVE-2024-0001",
        "severity": "HIGH",
        "package": "example-lib",
        "title": "Example high severity issue"
      }
    ]
  },
  "infrastructure": {
    "status": "unknown",
    "source": "terraform",
    "high_risk_change_detected": null
  },
  "history": {
    "status": "unknown",
    "similar_historical_failure": false,
    "rollback_required_recently": false,
    "is_synthetic": false
  },
  "missing_sources": [],
  "failed_sources": [],
  "is_synthetic": false
}
```

### 4.3 Source object rules

Every source block includes:

| Field | Required | Values |
|---|---|---|
| `status` | yes | `success` \| `failure` \| `unknown` |
| `source` | yes | `github` \| `github_actions` \| `trivy` \| `terraform` \| `ecs` \| `cloudwatch` \| `history` \| `synthetic` |

If a source is not in the first slice or failed to load:
- set `status: "unknown"`
- add the source name to `missing_sources` or `failed_sources`
- do not omit the block if the compact payload implied that category (CI, tests, Trivy counts)

### 4.4 GitHub fields

| Field | Required when `github.status=success` | Notes |
|---|---|---|
| `pull_request_number` | no | Null if the release is not PR-based |
| `first_commit_sha` | yes | First commit associated with the PR; lead-time start |
| `first_commit_at` | yes | Timestamp of that commit |
| `head_commit_sha` | yes | Must match `commit_sha` |
| `head_commit_at` | yes | |
| `authors` | no | |
| `changed_files_count` | yes | |
| `lines_changed` | no | Additions + deletions |
| `changed_files` | no | Paths used to detect migrations |
| `database_migration_detected` | yes | See section 6.3 |

If GitHub is `unknown`, lead time for this release is unavailable, not zero.

### 4.5 GitHub Actions fields

| Field | Required when `github_actions.status=success` |
|---|---|
| `ci_status` | yes (`success` \| `failure` \| `unknown`) |
| `test_status` | yes (`success` \| `failure` \| `unknown`) |
| `workflow_name` | no |
| `workflow_run_id` | no |
| `workflow_duration_seconds` | no |
| `deployment_workflow_status` | no; `unknown` until a deploy workflow exists |

`ci_status` is build/workflow outcome. `test_status` is the test job/step outcome. They may differ.

### 4.6 Trivy fields

| Field | Required when Trivy ran |
|---|---|
| `scan_status` | yes: `clean` \| `findings` \| `scan_failed` \| `unavailable` |
| `critical` / `high` / `medium` / `low` | yes when `scan_status` is `clean` or `findings`; integers ≥ 0 |
| `findings` | no; include id, severity, package when available |

`scan_failed` and `unavailable` are not `clean`. Counts must not be coerced to 0 in those states; leave counts null and treat evidence as missing.

### 4.7 Optional later source blocks

Present in the contract so later adapters do not break storage:

- `infrastructure` (Terraform): first slice may be `unknown`
- `deployment` (ECS): later slice
- `runtime` (CloudWatch): later slice
- `history`: synthetic allowed if `is_synthetic: true`

Missing Terraform/ECS/CloudWatch in the first slice is **not** “missing critical evidence.”

---

## 5. Missing and failed source behavior

### Critical sources for the first slice

These are required for a complete first-slice assessment:

1. `github`
2. `github_actions`
3. `trivy`

| Condition | `missing_sources` / `failed_sources` | Risk effect |
|---|---|---|
| Source not configured or not fetched | `missing_sources` | `missing_critical_evidence` if it is a critical source |
| Source fetched but errored | `failed_sources` | same as missing for scoring; distinct in UI/audit |
| Trivy `scan_failed` | `failed_sources: ["trivy"]` | not a clean scan; `missing_critical_evidence` applies |
| CI/test `unknown` | `missing_sources` or `failed_sources` as applicable | `missing_critical_evidence` applies; do not also treat as CI failure unless status is `failure` |

Non-critical sources (`terraform`, `ecs`, `cloudwatch`) may be `unknown` in the first slice with no `missing_critical_evidence` penalty.

---

## 6. Deterministic risk signals

### 6.1 Signal object

Every fired signal must be explainable:

```json
{
  "signal": "critical_vulnerability",
  "severity": "critical",
  "weight": 30,
  "evidence": "Trivy finding CVE-2024-0001",
  "source": "trivy",
  "deduplication_group": "security_critical"
}
```

| Field | Required | Purpose |
|---|---|---|
| `signal` | yes | Stable id from the catalog below |
| `severity` | yes | `low` \| `medium` \| `high` \| `critical` |
| `weight` | yes | Catalog weight |
| `evidence` | yes | Human-readable pointer to source evidence |
| `source` | yes | Evidence source |
| `deduplication_group` | yes | Signals in the same group count once |

### 6.2 Signal catalog (MVP weights)

| Signal | Weight | Dedup group | When it fires |
|---|---|---|---|
| `ci_failure` | +30 | `delivery_failure` | `ci_status` or `test_status` is `failure` |
| `critical_vulnerability` | +30 | `security_critical` | Trivy `critical >= 1` |
| `high_vulnerability` | +15 | `security_high` | Trivy `high >= 1` |
| `database_migration` | +15 | `schema_change` | `database_migration_detected` is true |
| `high_risk_infrastructure_change` | +15 | `infra_change` | Infrastructure adapter reports a high-risk change |
| `rollback_required` | +30 | `delivery_failure` | Rollback evidence for this release, or required by policy/history for this change |
| `similar_historical_failure` | +20 | `historical_similarity` | Historical matcher finds a similar failed/rolled-back release |
| `large_change_surface` | +10 | `change_surface` | See MVP constant below |
| `missing_critical_evidence` | +10 | `evidence_completeness` | Any first-slice critical source is missing or failed |

Multiple CVEs of the same severity fire the severity signal **once**, not once per CVE. Individual CVEs stay in `trivy.findings` for explanation.

### 6.3 Detection constants (tunable, documented)

**Database migration** is true if any changed file path matches:
- `**/migrations/**`
- `**/alembic/versions/**`
- `**/*migration*`

**Large change surface** is true if either:
- `changed_files_count >= 20`, or
- `lines_changed >= 500`

**High-risk infrastructure change** is not inferred in the first slice. It fires only when an infrastructure adapter (later Terraform) sets `high_risk_change_detected: true`.

### 6.4 Score formula

```text
applicable = unique signals after deduplication
  (for each deduplication_group, keep the single highest-weight signal)

risk_score = MIN(100, sum(applicable weights))
```

Dedup example: `ci_failure` (+30) and `rollback_required` (+30) share `delivery_failure`, so they contribute **+30 total**, not +60.

Worked example:

| Signal | Weight | Group |
|---|---|---|
| CI passed | 0 | — |
| Critical vulnerability | +30 | `security_critical` |
| DB migration | +15 | `schema_change` |
| Similar historical failure | +20 | `historical_similarity` |
| Large change surface | +10 | `change_surface` |

`risk_score = MIN(100, 75) = 75` → HIGH

### 6.5 Bands, recommendation, and enforcement

| Score | Level | Recommendation shown in UI |
|---|---|---|
| 0–30 | LOW | `ALLOW` |
| 31–60 | MEDIUM | `REQUIRE_HUMAN_REVIEW` |
| 61–100 | HIGH | `BLOCK_APPROVAL_REQUIRED` |

The recommendation is **not** an enforcement gate in the hackathon MVP.

- ReleaseGuard records the recommendation and the human Approve/Reject.
- It must not silently deploy.
- It must not claim it automatically stopped production until a later policy-gate task exists.
- UI copy for HIGH: **BLOCK / APPROVAL REQUIRED**, not “production was blocked by the platform.”

AI explains signals. AI must not change `risk_score`, fired signals, or the band.

---

## 7. Assessment result contract

```json
{
  "release_id": "REL-001",
  "risk_score": 75,
  "risk_level": "HIGH",
  "recommendation": "BLOCK_APPROVAL_REQUIRED",
  "enforcement": "none",
  "signals": [],
  "evidence_summary": {
    "ci_status": "success",
    "test_status": "success",
    "trivy": "findings",
    "history": "similar_failure"
  },
  "dora_context": {
    "window_days": 30,
    "trend_window_days": 7
  },
  "ai_explanation": {
    "status": "unknown",
    "text": null
  },
  "approval": {
    "state": "pending",
    "decision": null,
    "decided_at": null
  }
}
```

`approval.decision`: `approve` \| `reject` \| `null`  
`approval.state`: `pending` \| `approved` \| `rejected`  
`enforcement`: `none` for MVP

---

## 8. DORA event contract

### 8.1 Canonical `DeliveryEvent`

```json
{
  "event_id": "evt-001",
  "event_type": "DEPLOYMENT",
  "timestamp": "2026-08-16T14:00:00Z",
  "service": "releaseguard-ai",
  "project": "releaseguard-ai",
  "release_id": "REL-104",
  "environment": "production",
  "source": "github_actions",
  "is_synthetic": false,
  "metadata": {}
}
```

| Field | Required | Notes |
|---|---|---|
| `event_id` | yes | Unique |
| `event_type` | yes | Enum below |
| `timestamp` | yes | Event time, not ingest time |
| `service` | yes | |
| `project` | no | Defaults to `service` |
| `release_id` | no | Required for attributed CFR incidents and for linking lead time |
| `environment` | no | Qualifying DORA deploys are `production` |
| `source` | yes | `github` \| `github_actions` \| `ecs` \| `cloudwatch` \| `history` \| `synthetic` |
| `is_synthetic` | yes | |
| `metadata` | no | Type-specific fields |

Unknown data stays absent/null. Never convert missing counts or durations to 0.

### 8.2 Event types

| `event_type` | Meaning | Key metadata |
|---|---|---|
| `CODE_CHANGE` | A commit associated with a PR | `commit_sha`, `pull_request_number`, `is_first_commit_in_pr` |
| `DEPLOYMENT` | Qualifying production deployment | `deployment_status` (`success` \| `failure`), `commit_sha` |
| `DEPLOYMENT_FAILURE` | Failed production deployment | `commit_sha`, `reason` |
| `ROLLBACK` | Rollback of a production deployment | `rolled_back_release_id` |
| `INCIDENT_START` | Production incident begins | `incident_id`, attribution fields |
| `SERVICE_RESTORED` | Incident resolved / service restored | `incident_id` |

A failed production deploy may be recorded as `DEPLOYMENT` with `deployment_status=failure` **or** as `DEPLOYMENT_FAILURE`. Implementations must treat both as one failed deployment when `event_id`/`release_id` match; do not double-count.

### 8.3 Lead-time pairing

- Start: `CODE_CHANGE` where `is_first_commit_in_pr=true` for that PR
- End: successful production `DEPLOYMENT` for the same `release_id` or head commit
- If start or end is missing: lead time is `unavailable`, not 0
- If end timestamp is before start: invalid; exclude and record a validation error

### 8.4 Time windows

Every DORA response includes:

- `window_days: 30` (default)
- `trend_window_days: 7`
- `event_count` for the metric
- `unavailable: true` when source events are missing, distinct from a real zero

---

## 9. Incident attribution (CFR and MTTR)

Priority order:

1. **Explicit `release_id`** — primary, used for hackathon DORA
2. **Deployment timestamp correlation** — `LIKELY_RELATED`, not automatic causation
3. **Manual/synthetic association** — allowed only if `is_synthetic: true`

### 9.1 Attribution fields on `INCIDENT_START`

| Field | Required | Values |
|---|---|---|
| `incident_id` | yes | e.g. `INC-55` |
| `release_id` | no | e.g. `REL-104` |
| `attribution_method` | yes | `explicit_release_id` \| `timestamp_correlation` \| `synthetic` |
| `attribution_confidence` | yes | `attributed` \| `likely_related` \| `unknown` |

### 9.2 Rules

**Priority 1 — explicit `release_id`:**

```text
Deployment.release_id = REL-104
Incident.release_id   = REL-104
→ attribution_method = explicit_release_id
→ attribution_confidence = attributed
→ counts as a change failure for that deployment
```

**Priority 2 — timestamp correlation:**

MVP constant: incident timestamp is within **30 minutes after** a production deployment timestamp.

```text
Deployment 14:00, Incident 14:08 → likely_related
Deployment 14:00, Incident 22:00 → unknown (needs more evidence)
```

`likely_related` may be shown as context to the approver and to AI. It does **not** automatically count as CFR failure.

**Priority 3 — synthetic:**

Demo incidents should still carry `release_id` so DORA stays clean. They must set `is_synthetic: true` and `attribution_method: synthetic` or `explicit_release_id` with `is_synthetic: true`.

### 9.3 CFR counting

A qualifying production deployment is a change failure if **any one** of these is associated with it:
- `DEPLOYMENT_FAILURE` or `DEPLOYMENT.deployment_status=failure`
- `ROLLBACK`
- `INCIDENT_START` with `attribution_confidence=attributed`

Count that deployment once.

`likely_related` and `unknown` incidents do not increment CFR. They also do not prove the deploy succeeded.

### 9.4 MTTR

- Start: `INCIDENT_START.timestamp`
- End: matching `SERVICE_RESTORED.timestamp` for the same `incident_id`
- Open incident (no restore): duration `unavailable` / open, not 0
- Restore before start: invalid; exclude

---

## 10. First-slice vs later sources

| Source | First slice | Later |
|---|---|---|
| GitHub | yes | — |
| GitHub Actions | yes | — |
| Trivy | yes | — |
| Labeled synthetic history/incidents | yes, for DORA demo | — |
| ECS / ECR | no | deployment events, progressive delivery |
| CloudWatch | no | error rate / latency / rollback context |
| Terraform | no | high-risk infra signal |
| Argo Rollouts, OPA/Kyverno, SBOM, Cosign | no | future SOTA candidates; not current work |

Until ECS exists, DORA `DEPLOYMENT` events may come from:
- a GitHub Actions deployment workflow, if present, and/or
- labeled synthetic deployment events

---

## 11. API operations

RG-003 paths:

- `GET /health`
- `GET /ready`
- `POST /v1/releases` — expand compact or canonical evidence, persist, return `{ evidence, assessment }`
- `GET /v1/releases/{release_id}` — retrieve stored evidence
- `GET /v1/releases/{release_id}/assessment` — deterministic risk score, signals, recommendation
- `POST /v1/releases/{release_id}/approval` — record `approve` or `reject` (does not change risk score)

Later tasks add:
- Get DORA metrics for 30-day and 7-day windows
- Get delivery events for a release

---

## 12. Out of contract for RG-002

Not defined here and not to be invented during RG-002:
- HTTP path names and auth headers
- PostgreSQL table DDL
- Groq prompt text
- ECS task definition
- Dashboard component structure beyond the `/dashboard` information content already decided
