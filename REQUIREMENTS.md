# ReleaseGuard AI — Requirements

## Functional Requirements

### FR-001 — Release Evidence Collection
**Status:** TODO

Accept release evidence from configured DevOps sources.

**Acceptance criteria:**
- Evidence is associated with a release.
- Missing evidence is explicit.
- Source and timestamp/context are retained where available.

### FR-002 — CI/CD Result Awareness
**Status:** TODO

Consume build, test, workflow, and deployment outcomes.

**Acceptance criteria:**
- Passed, failed, and unknown states are distinct.
- Failed/missing evidence cannot be represented as passed.

### FR-003 — Security Risk Evidence
**Status:** TODO

Incorporate scanner findings.

**Acceptance criteria:**
- Severity and source are retained.
- Findings contribute risk signals.
- Scanner failure is distinct from a clean scan.

### FR-004 — Infrastructure/Deployment Context
**Status:** TODO

Incorporate relevant infrastructure and deployment changes.

**Acceptance criteria:**
- Changes are associated with a release.
- Unknown deployment context is not silently treated as safe.

### FR-005 — Historical Operational Context
**Status:** TODO

Support prior releases, incidents, rollbacks, and related operational records.

**Acceptance criteria:**
- Historical records can be associated with service/change type.
- Synthetic records are explicitly labeled.
- No fabricated enterprise history is presented as real.

### FR-006 — Deterministic Risk Assessment
**Status:** TODO

Apply explicit and inspectable release-risk rules.

**Acceptance criteria:**
- Rules are inspectable.
- Rule results trace to evidence.
- Core safety checks do not depend on an LLM.
- Signals use the catalog, weights, and deduplication groups in `CONTRACTS.md`.

### FR-007 — AI-Assisted Explanation
**Status:** TODO

Use an AI/LLM component to explain contextual risk from supplied evidence.

**Acceptance criteria:**
- Output is grounded in evidence.
- Missing context is acknowledged.
- No certainty about future incidents is claimed.
- AI failure is represented as unavailable/error.

### FR-008 — Human Approval Recommendation
**Status:** TODO

Produce:
- risk level/score,
- findings,
- recommendation,
- supporting evidence.

Required concepts:
- Allow.
- Require human review.
- Block.

**MVP score bands (ADR-012 / ADR-023):**
- 0–30: LOW → ALLOW
- 31–60: MEDIUM → REQUIRE HUMAN REVIEW
- 61–100: HIGH → BLOCK / APPROVAL REQUIRED

The 0–100 score is the capped sum of catalog weights after deduplication (`CONTRACTS.md`). AI does not change the score.

The recommendation is distinct from enforcement. MVP `enforcement` is `none`; the UI must not claim production was automatically stopped.

The final approval remains human-controlled. ReleaseGuard must record Approve or Reject against the assessment.

### FR-009 — Auditability
**Status:** TODO

Retain sufficient assessment context to explain why a recommendation was produced.

---

## DORA Requirements

### FR-010 — DORA Event Model
**Status:** TODO

Create a normalized event model capable of representing:
- deployment events,
- code-change/commit events,
- release outcome/failure events,
- incident start events,
- incident recovery/restore events.

**Acceptance criteria:**
- Events have timestamps.
- Events can be associated with a service/project/release where possible.
- Source is retained.
- Unknown data is not converted into zero.

### FR-011 — Deployment Frequency
**Status:** TODO

Calculate deployment frequency for a defined time window.

**Definition for MVP:**
Number of qualifying production deployments in the selected time window.

**Windows (ADR-014):**
- Default: 30 days.
- Trend: 7 days.

**Acceptance criteria:**
- Time window is explicit.
- Deployment count is visible.
- Source events are traceable.

### FR-012 — Lead Time for Changes
**Status:** TODO

Calculate lead time from qualifying code change/commit to production deployment.

**MVP definition (ADR-015):**
Start = first commit associated with the pull request.  
End = production deployment.

**Acceptance criteria:**
- Start and end event definitions are explicit.
- Timestamp ordering is validated.
- Aggregation method is documented.
- Unmatched events are handled explicitly.

### FR-013 — Change Failure Rate
**Status:** TODO

Calculate the proportion of qualifying production deployments that result in a defined failure outcome.

**MVP attribution policy (ADR-013):**
A qualifying production deployment is a change failure if any of the following is associated with that release/deployment:
- failed deployment,
- rollback,
- production incident attributable to the release.

Count a deployment once even if more than one failure outcome applies.

An incident counts toward CFR only when `attribution_confidence=attributed` (explicit `release_id`). Timestamp `likely_related` incidents are context only.

If attribution cannot be determined, treat the outcome as unknown/unavailable, not zero and not success.

See `CONTRACTS.md` section 9.

### FR-014 — Time to Restore Service
**Status:** TODO

Calculate time from qualifying incident start to service restoration.

**Acceptance criteria:**
- Start and recovery events are explicit.
- Unresolved incidents are handled as open/unknown rather than zero.
- Aggregation method is documented.

### FR-015 — DORA Context in Release Assessment
**Status:** TODO

Make relevant DORA context available to ReleaseGuard risk analysis.

**Example:**
A current high-complexity release from a service with elevated recent change-failure rate may receive additional review context.

**Guardrail:** DORA metrics must not automatically prove that a release is unsafe.

### FR-016 — DORA Dashboard
**Status:** TODO

Provide a concise view of the four DORA metrics, the 30-day default window, the 7-day trend, and underlying event counts.

---

## SOTA Capability Requirements

### FR-017 — Evidence Aggregation
**Status:** TODO

Combine delivery, security, infrastructure, historical, DORA, and runtime evidence into a normalized release context.

### FR-018 — Historical Pattern Detection
**Status:** TODO

Identify relevant similarities between the current release and prior releases/incidents.

### FR-019 — Explainable AI
**Status:** TODO

AI explanations must identify the evidence behind important claims.

### FR-020 — Human-in-the-Loop Governance
**Status:** TODO

The primary workflow shall present the recommendation to a human approver rather than silently deploy.

ReleaseGuard must record the human decision as Approve or Reject against the assessment.

### FR-021 — Post-Release Feedback
**Status:** BACKLOG

Where runtime/deployment data is available, associate release outcomes with historical context for future analysis.

### FR-022 — Release Intelligence View
**Status:** TODO

The first UI is `/dashboard` only and shall contain:
- DORA delivery health,
- current release risk,
- important findings,
- historical context when available,
- AI recommendation,
- approval state with Approve/Reject.

---

## Non-Functional Requirements

### NFR-001 — Security
- No hard-coded secrets.
- Appropriate secret handling.
- Minimize sensitive data in logs/prompts.

### NFR-002 — Explainability
- Risk findings identify evidence.
- DORA metrics identify source/time window.
- AI explanations are grounded.

### NFR-003 — Reliability
- Source/AI failures are unknown/unavailable, not safe.

### NFR-004 — Observability
- Important application, ingestion, DORA calculation, and assessment failures are observable.

### NFR-005 — Performance
Exact targets: UNKNOWN — requires confirmation.

### NFR-006 — Scalability
Exact targets: UNKNOWN — requires confirmation.

### NFR-007 — Privacy
Minimize unnecessary data transfer/retention.

### NFR-008 — AI Quality
Test grounding, hallucination, missing context, failure behavior, and prompt injection where applicable.

### NFR-009 — Metric Integrity
DORA calculations must be deterministic, traceable, reproducible, and tested against known examples.
