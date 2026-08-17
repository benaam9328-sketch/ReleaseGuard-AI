# ReleaseGuard AI — Architecture & Product Decisions

## ADR-001 — ReleaseGuard Is a Governance Layer

**Status:** Accepted  
**Date:** 2026-08-09

ReleaseGuard sits around normal CI/CD and staging and provides contextual release intelligence. It does not replace CI/CD, QA, or human approval.

---

## ADR-002 — Deterministic Risk Rules + AI Explanation

**Status:** Accepted

Deterministic risk signals provide inspectable safety logic. AI provides contextual interpretation and explanation.

AI is not the sole source of truth.

---

## ADR-003 — Existing DevOps Systems Are Data Sources

**Status:** Accepted

ReleaseGuard consumes evidence from existing systems instead of recreating them.

---

## ADR-004 — Synthetic Historical Data Is Allowed for the Hackathon

**Status:** Accepted for MVP demonstration

Synthetic historical releases/incidents may be used if clearly labeled and never represented as real enterprise history.

---

## ADR-005 — Keep the Integration Surface Small

**Status:** Accepted in principle

Start with a small number of high-value integrations and expand only after the core workflow works.

---

## ADR-006 — DORA Is a Separate Delivery-Performance Layer

**Status:** Accepted  
**Date:** 2026-08-16

### Context
ReleaseGuard needs both delivery-performance visibility and release-risk intelligence.

### Decision
Implement the four initial DORA metrics as a separate measurement layer:
- Deployment Frequency.
- Lead Time for Changes.
- Change Failure Rate.
- Time to Restore Service.

DORA metrics can provide context to release-risk analysis but are not themselves a release-risk score.

### Reason
This keeps industry-recognized delivery measurement conceptually separate from the product's contextual release-risk engine.

### Consequences
We need a normalized delivery/incident event model and explicit metric definitions.

---

## ADR-007 — SOTA Means Capability Set, Not a Proprietary Score

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
The project will use “SOTA” to describe modern/state-of-the-art release-intelligence capabilities rather than inventing a fifth standardized metric or unsupported numerical score.

Capabilities include:
- AI-assisted analysis.
- Historical pattern detection.
- Evidence aggregation.
- DORA-aware context.
- Security and IaC context.
- Deployment/runtime health.
- Explainability.
- Human-in-the-loop governance.

### Reason
A capability-based definition is more technically defensible and easier to demonstrate.

---

## ADR-008 — Human Approval Is the Primary Workflow

**Status:** Accepted  
**Date:** 2026-08-16

ReleaseGuard primarily assists a human release approver.

The system recommendation may be ALLOW, REVIEW, or BLOCK, but the MVP does not silently deploy to production.

The human decision is recorded in ReleaseGuard as Approve or Reject, with enough context to audit it later.

### Reason
This matches organizations where every production release already requires approval and makes the product useful without assuming autonomous operations.

---

## ADR-009 — LLM Provider Is Groq

**Status:** Accepted (model updated 2026-08-17)  
**Date:** 2026-08-16

### Decision
Use Groq as the LLM provider for grounded AI explanation.

The original model was Llama 3.3 70B (`llama-3.3-70b-versatile`). Groq retired that model on 2026-08-16. The current model id is `openai/gpt-oss-20b` so the hackathon demo stays on Groq's Free plan. Override with `GROQ_MODEL` if needed.

The AI still receives structured evidence and deterministic risk signals. It does not independently invent facts or override safety evidence.

### Reason
One provider for the MVP. Groq is suitable for a live demo because of low latency. The model id had to change after the Llama 3.3 shutdown.

---

## ADR-010 — Frontend Is Next.js + React

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
The dashboard is a Next.js + React application. FastAPI remains the backend/API.

One primary frontend framework for the MVP.

---

## ADR-011 — Persistence Is PostgreSQL

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
Use PostgreSQL to persist:
- normalized release evidence,
- DORA events,
- assessment history,
- synthetic historical records (explicitly labeled),
- human approval decisions (Approve/Reject).

Local development should use PostgreSQL via Docker Compose unless a later decision says otherwise.

### Reason
The MVP now has a justified persistence use case: assessments, DORA events, history, and recorded approvals must survive process restarts and be auditable.

---

## ADR-012 — Initial Risk Score Thresholds

**Status:** Accepted for MVP; validate with scenarios  
**Date:** 2026-08-16

### Decision
Map a 0–100 deterministic risk score as follows:
- **0–30:** ALLOW / LOW RISK
- **31–60:** REQUIRE HUMAN REVIEW / MEDIUM RISK
- **61–100:** BLOCK / HIGH RISK

The scoring formula that produces the 0–100 value is still to be defined during risk-engine implementation and must be validated against the three required demo scenarios (allow, review, block).

AI explanation must not change the score.

---

## ADR-013 — Change Failure Rate Attribution Policy

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
A qualifying production deployment counts as a change failure if any of the following is associated with that release/deployment:
- failed deployment,
- rollback,
- production incident attributable to the release.

A deployment is counted once even if more than one failure outcome applies.

If attribution cannot be determined, the outcome is unknown/unavailable, not a zero failure and not a success.

---

## ADR-014 — DORA Time Window

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
- Default calculation window: **30 days**.
- Additional trend window: **7 days**.

Every DORA result must include the window, event counts, and source context.

---

## ADR-015 — Lead Time Start Event

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
Lead Time for Changes starts at the **first commit associated with the pull request** and ends at **production deployment**.

Unmatched commits or deployments are handled explicitly and are not converted into a zero lead time.

---

## ADR-016 — AWS Evidence for MVP

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
Use real AWS deployment/runtime evidence where practical.

If a live AWS signal is not available, use synthetic fallback data that is clearly labeled as synthetic.

---

## ADR-017 — Hackathon Auth

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
No user login for the hackathon MVP.

Secrets, tokens, and APIs must still be protected: no hard-coded secrets, no public exposure of keys, and no unnecessary sensitive data in logs or AI prompts.

---

## ADR-018 — Python and FastAPI Versions

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
- Python **3.12**
- Current stable FastAPI compatible with Python 3.12

---

## ADR-019 — Demo Format

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
Primary demo is a live UI and live workflow.

A recorded walkthrough is the fallback if a live demo is not possible.

---

## ADR-020 — GitHub Scope Starts With One Configured Repo

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
Start with one configured repository as the GitHub evidence source.

Design the GitHub adapter so additional repositories can be added later without rewriting the release-evidence contract.

---

## ADR-021 — First Evidence Slice Is GitHub + GitHub Actions + Trivy

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
The first complete vertical slice is:

`GitHub → GitHub Actions (build + test) → Trivy → ReleaseGuard → risk assessment`

AWS/ECS is not required to prove the risk engine.

Normalized contracts live in `CONTRACTS.md`.

---

## ADR-022 — Deterministic Risk Score Catalog

**Status:** Accepted for MVP; validate with scenarios  
**Date:** 2026-08-16

### Decision
Score = `MIN(100, sum of applicable signal weights)` after deduplication.

MVP catalog:
- CI/CD failure: +30 (`delivery_failure`)
- Critical vulnerability: +30 (`security_critical`)
- High vulnerability: +15 (`security_high`)
- Database migration: +15 (`schema_change`)
- High-risk infrastructure change: +15 (`infra_change`)
- Rollback required: +30 (`delivery_failure`)
- Similar historical failure: +20 (`historical_similarity`)
- Large change surface: +10 (`change_surface`)
- Missing critical evidence: +10 (`evidence_completeness`)

Signals in the same `deduplication_group` count once, using the highest weight in that group.

Each fired signal stores `signal`, `severity`, `weight`, `evidence`, `source`, and `deduplication_group`.

Detection constants and examples are in `CONTRACTS.md`.

AI must not change the score.

---

## ADR-023 — Recommendation Is Distinct From Enforcement

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
HIGH (61–100) is shown as **BLOCK / APPROVAL REQUIRED**.

This is a recommendation plus a recorded human Approve/Reject. It is not an automatic production stop in the hackathon MVP.

`enforcement` remains `none` until a later policy-gate task exists.

---

## ADR-024 — Incident Attribution Order

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
1. Explicit `release_id` → `attributed` (counts toward CFR). This is the hackathon demo path.
2. Timestamp correlation within 30 minutes after deployment → `likely_related` (context only; not automatic CFR).
3. Manual/synthetic association only if labeled `is_synthetic: true`.

`likely_related` must not be stored or displayed as “caused by.”

---

## ADR-025 — AWS Deployment Target Is ECS

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
Later deployment/runtime path:

`Docker build → ECR → ECS → CloudWatch`

ECS is not part of the first evidence slice. If live ECS/CloudWatch data is unavailable, use labeled synthetic fallback.

EC2, Lambda, and Elastic Beanstalk are not the MVP deployment target.

---

## ADR-026 — Frontend Is Next.js App Router + Tailwind

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
Use Next.js App Router, React, and Tailwind.

First UI is `/dashboard` only, showing DORA, current release risk, evidence status, AI recommendation, and Approve/Reject.

Planned later routes (`/releases`, `/dora`, `/deployments`, `/incidents`, `/risk`, `/settings`) are not current work.

---

## ADR-027 — Later SOTA Candidates Are Not Current Work

**Status:** Accepted  
**Date:** 2026-08-16

### Decision
Do not implement the following until explicitly pulled into an approved task:
- Argo Rollouts / progressive delivery
- OPA/Kyverno policy-as-code enforcement
- SBOM
- Cosign

The first coding task after this contract is RG-003 (minimal application), not the full platform.
