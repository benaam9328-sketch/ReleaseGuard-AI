# ReleaseGuard AI — Current Project Context

## Current Development Phase

**Incremental implementation**

## Current Implementation Status

- Application code: FastAPI bootstrap started (RG-003).
- Evidence contract models + compact expansion: DONE.
- Deterministic risk engine: DONE (RG-008).
- Persistence: in-memory fallback; PostgreSQL via Docker Compose when `DATABASE_URL` is set.
- DORA implementation: DONE (RG-011 to RG-016). DORA is not the risk score.
- AI integration: DONE (RG-009 Groq explanation; score stays deterministic).
- AWS/ECS deployment: NOT STARTED.
- Historical integration: DONE (RG-018 / RG-025 labeled synthetic matcher).
- Dashboard: DONE (`/dashboard` only).
- Demo seed: DONE (`POST /v1/demo/seed` plus dashboard **Create demo release**).
- RG-002 contracts: COMPLETE (`CONTRACTS.md`).
- RG-003 bootstrap: COMPLETE.
- RG-008 risk engine: COMPLETE.
- RG-010 human approval: COMPLETE.
- RG-007 GitHub / Actions / Trivy adapters: COMPLETE.
- RG-005 / RG-006 Docker image and GitHub Actions CI: COMPLETE.
- RG-009 Groq / Llama explanation: COMPLETE.
- RG-011 to RG-016 DORA engine: COMPLETE.
- RG-018 / RG-025 labeled synthetic history matching: COMPLETE.

## Current Task

**Phase 8** next: AWS demo (ECS / ECR / CloudWatch) if needed. Do not generate extra SOTA tools.

## Current Unknowns

- Python 3.12 is the project target; this machine currently ran tests on Python 3.10.
- Docker Desktop was not running locally when the image was added; GitHub Actions builds the image.
- Exact performance targets.

## Immediate Next Steps

1. Rebuild Compose API, open `/dashboard`, click **Create demo release**.
2. Confirm DORA is populated and labeled synthetic; Groq either explains or shows a clear missing-key message.
3. Next product slice: AWS ECS / ECR / CloudWatch (RG-023, RG-024, RG-027).

## Established Product Direction

- ReleaseGuard is a release-risk/governance layer, not a staging replacement.
- Existing DevOps tools are the primary evidence sources.
- Human approval is the primary workflow; Approve/Reject is recorded in ReleaseGuard.
- Deterministic risk rules and AI explanation are separate layers.
- DORA is a delivery-performance layer.
- SOTA is a capability set, not a numerical metric.
- Synthetic historical data may be used for a clearly labeled hackathon demo.
- Recommendation is distinct from enforcement. HIGH means BLOCK / APPROVAL REQUIRED, not an automatic production stop.

## Locked MVP Decisions (2026-08-16)

- LLM: Groq + `openai/gpt-oss-20b` (Free plan; Llama 3.3 70B retired 2026-08-16).
- Frontend: Next.js App Router + React + Tailwind; first UI `/dashboard`.
- Persistence: PostgreSQL.
- First evidence slice: GitHub + GitHub Actions + Trivy.
- Risk bands: 0–30 ALLOW, 31–60 REVIEW, 61–100 BLOCK / APPROVAL REQUIRED.
- Score: capped sum of catalog weights after `deduplication_group`.
- CFR: failed deploy + rollback + incident with explicit `release_id`.
- Timestamp correlation (30 minutes) is `likely_related` only, not automatic CFR.
- DORA windows: 30-day default + 7-day trend.
- Lead time: first PR-associated commit → production deployment.
- AWS later path: ECS + ECR + CloudWatch; labeled synthetic fallback if needed.
- Auth: no login for hackathon MVP; protect secrets/APIs.
- Runtime: Python 3.12 + current stable FastAPI.
- Demo: live UI + live workflow; recorded fallback.
- GitHub: one configured repo first; adapter designed for more later.

## DORA Scope

Initial metrics:
1. Deployment Frequency.
2. Lead Time for Changes.
3. Change Failure Rate.
4. Time to Restore Service.

DORA should provide context to release-risk analysis, not become the release-risk score itself.

## SOTA Capability Scope

The project should demonstrate modern release-intelligence capabilities:
- multi-source evidence aggregation,
- AI-assisted risk explanation,
- historical pattern detection,
- security/IaC context,
- DORA-aware analysis,
- deployment/runtime feedback,
- explainability,
- human-in-the-loop governance.

Not current work: Argo Rollouts, OPA/Kyverno, SBOM, Cosign.

## Not Currently Being Built

- Full enterprise ServiceNow/Jira integration.
- Full Kubernetes/EKS implementation.
- Autonomous production deployment / policy-gate enforcement.
- Custom AI model training/fine-tuning.
- Unsupported SOTA score.
- Large-scale enterprise analytics.
- Argo Rollouts, OPA/Kyverno, SBOM, Cosign.
- Extra dashboard routes beyond `/dashboard`.
