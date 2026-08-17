# ReleaseGuard AI — Architecture

## Architecture Status

The project is moving from architecture definition into incremental implementation.

The architecture below is the approved conceptual target. Individual components remain TODO until implemented.

Normalized contracts: `CONTRACTS.md`.

## First Vertical Slice

```text
GitHub
  → GitHub Actions (build + test)
  → Trivy
  → ReleaseGuard
       ├── Evidence
       ├── DORA (events may be Actions + labeled synthetic until ECS)
       └── Risk rules
  → AI analysis (later task)
  → Human approval (recorded)
```

ECS → CloudWatch is a later slice, not required to prove the risk engine.

## High-Level Architecture

```text
                         ┌──────────────────────┐
                         │      DEVOPS SOURCES  │
                         ├──────────────────────┤
                         │ GitHub / GitHub API   │
                         │ GitHub Actions       │
                         │ Trivy                │
                         │ Terraform            │
                         │ AWS / CloudWatch     │
                         │ Incident/History     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Evidence Ingestion   │
                         │ & Normalization      │
                         └──────────┬───────────┘
                                    │
                         ┌──────────┴───────────┐
                         │                      │
                         ▼                      ▼
                ┌──────────────────┐   ┌──────────────────┐
                │ DORA Engine      │   │ Release Risk     │
                │                  │   │ Engine            │
                │ DF               │   │ Code/change      │
                │ Lead Time        │   │ Security         │
                │ CFR              │   │ IaC/deployment   │
                │ MTTR             │   │ History          │
                └────────┬─────────┘   └────────┬─────────┘
                         │                      │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Release Intelligence │
                         │ Context              │
                         └──────────┬───────────┘
                                    │
                           ┌────────┴────────┐
                           ▼                 ▼
                    Deterministic       AI/LLM Analysis
                    Risk Signals              │
                           │                   │
                           └─────────┬─────────┘
                                     ▼
                         ┌──────────────────────┐
                         │ Recommendation       │
                         │ ALLOW / REVIEW /     │
                         │ BLOCK                │
                         └──────────┬───────────┘
                                    ▼
                             Human Approver
                                    │
                                    ▼
                              Production
                                    │
                                    ▼
                         Runtime/Incident Data
                                    │
                                    └──────► Historical Feedback
```

## Architectural Layers

### 1. Evidence Adapters

Retrieve or receive source-specific evidence and convert it into common contracts.

Candidate sources for the full product:
- GitHub and GitHub Actions (first slice).
- Trivy (first slice).
- Terraform (later).
- AWS ECS / ECR (later).
- CloudWatch (later).
- Historical/incident data (labeled synthetic allowed for demo).

### 2. Release Context / Normalization

Combine evidence into a stable release context.

Unknown data must remain explicit.

### 3. DORA Engine

Calculates:
- Deployment Frequency.
- Lead Time for Changes.
- Change Failure Rate.
- Time to Restore Service.

The engine should operate from normalized events and explicit definitions.

### 4. Deterministic Risk Engine

Applies inspectable risk rules from `CONTRACTS.md`.

DORA metrics may provide contextual signals but must not be treated as direct proof of release failure.

Score = `MIN(100, sum of deduplicated signal weights)`.

### 5. Historical Context

Provides previous release, incident, rollback, and change-pattern evidence.

Synthetic data is allowed for the hackathon if clearly labeled.

### 6. AI/LLM Analysis

Receives structured evidence and risk signals.

Responsibilities:
- explain important risks,
- correlate evidence,
- summarize historical context,
- explain recommendation rationale.

AI does not independently invent facts or silently override deterministic evidence.

### 7. Decision/Policy Layer

Maps configured risk evidence into:
- ALLOW,
- REQUIRE HUMAN REVIEW,
- BLOCK / APPROVAL REQUIRED.

**MVP thresholds (ADR-012 / ADR-023):**
- 0–30: ALLOW / LOW
- 31–60: REQUIRE HUMAN REVIEW / MEDIUM
- 61–100: BLOCK / APPROVAL REQUIRED / HIGH

The 0–100 score comes from deterministic rules. AI does not change the score.

Recommendation and enforcement are distinct. MVP enforcement is `none`.

### 8. Human Approval Layer

Primary target workflow:

`ReleaseGuard recommendation → human review → approve/reject`

The Approve/Reject decision is recorded in ReleaseGuard.

No user login for the hackathon MVP. Secrets and APIs still require protection.

The HIGH recommendation does not automatically stop production in the MVP.

Autonomous production deployment is not the MVP goal.

### 9. Post-Release Feedback

Future layer:
- deployment health,
- error rate,
- latency,
- incidents,
- rollback,
- restoration.

These outcomes can enrich historical context and future risk analysis.

## DORA Data Model

Canonical fields and event types are defined in `CONTRACTS.md`.

Conceptual normalized events:

```text
DeliveryEvent
- event_id
- event_type
- timestamp
- service
- project
- release_id
- environment
- source
- is_synthetic
- metadata
```

Event types:
- CODE_CHANGE
- DEPLOYMENT
- DEPLOYMENT_FAILURE
- ROLLBACK
- INCIDENT_START
- SERVICE_RESTORED

Incident attribution order: explicit `release_id` → 30-minute timestamp `likely_related` → labeled synthetic.

## DORA Calculation Flow

```text
Source Events
     ↓
Normalize
     ↓
Filter qualifying events
     ↓
Apply explicit time window (30-day default + 7-day trend)
     ↓
Calculate DORA metric
     ↓
Return value + event counts + window + source context
```

## SOTA Capability Model

SOTA is not represented as one number.

Instead, the platform demonstrates modern release-intelligence capabilities:
- AI-assisted reasoning.
- Historical similarity.
- Multi-source evidence aggregation.
- DORA-aware context.
- Security/IaC awareness.
- Deployment health.
- Explainable recommendations.
- Human-in-the-loop governance.

## API Direction

Exact endpoint names remain implementation decisions.

Conceptual operations:
- Submit/analyze release.
- Retrieve release assessment.
- Retrieve evidence.
- Retrieve DORA metrics.
- Retrieve historical context.
- Retrieve approval/recommendation state.

## Architecture Guardrails

- Keep DORA and release risk as distinct concepts.
- Do not couple DORA calculations directly to an LLM.
- Do not let missing events become zero-valued metrics.
- Preserve event timestamps and source information.
- Keep AI grounded in structured evidence.
- PostgreSQL is the approved persistence store; do not add a second database.
- Do not add Kubernetes solely for technology count.
- Do not implement Argo Rollouts, OPA/Kyverno, SBOM, or Cosign until an approved task pulls them in.
