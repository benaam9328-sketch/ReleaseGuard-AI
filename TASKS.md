# ReleaseGuard AI — Task Backlog

## Completed

### RG-001 — Establish Project Context
**Status:** COMPLETE

Project documentation, architecture principles, DORA positioning, SOTA capability model, and agent guardrails are established.

### RG-002 — Confirm MVP and Release Evidence Contract
**Status:** COMPLETE

Normalized release evidence, risk-signal catalog, and DORA event contracts are in `CONTRACTS.md`.

### RG-003 — Bootstrap Minimal Application
**Status:** COMPLETE

Minimal FastAPI app with contract models, compact→canonical expansion, `/v1/releases` persistence, health/ready, Docker Compose PostgreSQL, and bootstrap tests.

### RG-008 — Implement Deterministic Risk Engine
**Status:** COMPLETE

Inspectable signal catalog, deduplication groups, 0–100 score, LOW/MEDIUM/HIGH bands, and `GET /v1/releases/{id}/assessment`. Enforcement remains `none`.

### RG-010 — Add Human Approval Recommendation
**Status:** COMPLETE

Record Approve/Reject against a release. Recommendation bands already come from the risk engine. Enforcement remains `none`.

### RG-007 — Add Security Evidence
**Status:** COMPLETE

GitHub commit/PR, GitHub Actions, and Trivy JSON adapters enrich `POST /v1/releases`. Failed fetches stay `unknown`; a missing Trivy `Results` block is `scan_failed`, not a clean scan.

### RG-005 — Containerize Application
**Status:** COMPLETE

Python 3.12 image runs uvicorn on port 8000. `docker compose up --build` starts the API with Postgres.

### RG-006 — Add GitHub Actions CI
**Status:** COMPLETE

On `master`, CI installs dependencies, runs pytest, and builds the Docker image. It does not deploy.

### RG-009 — Add AI-Assisted Explanation
**Status:** COMPLETE

Groq explains the deterministic assessment (`openai/gpt-oss-20b`, Free plan). Missing or failed Groq calls stay `unknown`/`failure`. The model cannot change `risk_score`.

### RG-011 — Define DORA Event Model
**Status:** COMPLETE

`DeliveryEvent` ingest via `POST /v1/events`.

### RG-012 — Implement Deployment Frequency
**Status:** COMPLETE

Production deployments in the 30-day window; 7-day trend. Empty history is `unavailable`, not zero.

### RG-013 — Implement Lead Time for Changes
**Status:** COMPLETE

First PR-associated commit to successful production deploy. Missing start/end is `unavailable`, not 0.

### RG-014 — Implement Change Failure Rate
**Status:** COMPLETE

Failed deploy, rollback, or attributed incident. `likely_related` does not increment CFR. One deployment is counted once.

### RG-015 — Implement Time to Restore Service
**Status:** COMPLETE

Incident start to matching restore. Open or reversed incidents are not zero.

### RG-016 — Add DORA Context to Release Analysis
**Status:** COMPLETE

`assessment.dora_context.snapshot` is attached to release analysis. It does not change `risk_score`.

### RG-018 — Historical Pattern Detection
**Status:** COMPLETE

Current release is compared to labeled synthetic similar-failure records (migration or matching vuln severity).

### RG-025 — Historical Incident Adapter
**Status:** COMPLETE

Seed records in `app/history/synthetic_records.json` set `is_synthetic: true`. Empty catalog stays `unknown`, not a clean history.

## Current

### RG-004 — Add Automated Tests
**Status:** READY  
**Priority:** P0

Test core service behavior.

Bootstrap tests for health, validation, and evidence expansion landed with RG-003. Risk-engine contract cases landed with RG-008. Remaining coverage follows each new engine.

## DORA Workstream

### RG-017 — Build DORA Dashboard
**Priority:** P1

Display four metrics, trends/time window, and event counts.

## SOTA Capability Workstream

### RG-019 — Multi-Source Release Intelligence
**Priority:** P1

Combine DORA, security, infrastructure, deployment, and historical evidence.

### RG-020 — Explainable Recommendation View
**Priority:** P1

Present evidence → signal → explanation → recommendation.

### RG-021 — Post-Release Feedback
**Priority:** P2

Associate deployment/runtime outcomes with historical context.

## Infrastructure

### RG-022 — Terraform Change Evidence
**Priority:** P1

### RG-023 — AWS Deployment/Runtime Evidence
**Priority:** P1

ECS + ECR. Labeled synthetic fallback if live evidence is unavailable.

### RG-024 — Observability/CloudWatch Context
**Priority:** P1

### RG-026 — Unified Release Intelligence Dashboard
**Status:** COMPLETE

`/dashboard` shows DORA, risk, findings, labeled history, AI explanation, and Approve/Reject.

## Product

### RG-027 — Production-Like Demo Workflow
**Priority:** P1

Demonstrate:

`GitHub → GitHub Actions → Trivy → ReleaseGuard → human approval → ECS → CloudWatch`

First-slice demo can stop at recorded approval before ECS exists.

## Later SOTA Candidates (not current)

Do not start these until explicitly approved:
- Progressive delivery / Argo Rollouts
- Policy-as-code enforcement / OPA or Kyverno
- SBOM
- Cosign

## Backlog Discipline

Do not add detailed implementation tasks without a corresponding requirement or architecture decision.
