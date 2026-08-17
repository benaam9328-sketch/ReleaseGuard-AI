# ReleaseGuard AI — Master AI Agent Instructions

> **Target audience:** Cursor, Codex, Claude Code, AI pair programmers, developers, and DevOps engineers.
> **Project:** ReleaseGuard AI
> **Hackathon:** YMSLI AI Hackathon 2026
> **Last updated:** August 2026

## 1. Mission

ReleaseGuard AI is an intelligent release-risk and governance layer that sits around the existing software delivery process.

It does **not** replace CI/CD, staging, QA, monitoring, or human release approval.

It combines:
- release evidence from DevOps systems,
- deterministic release-risk rules,
- DORA delivery-performance metrics,
- historical operational context,
- security and infrastructure evidence,
- deployment/runtime health,
- and AI-assisted contextual reasoning

to help a human approver make a faster, better-informed release decision.

### Core product statement

> **ReleaseGuard does not replace the person approving a release; it gives that person the intelligence needed to approve it confidently.**

## 2. DORA and SOTA Positioning

### DORA

DORA is a **delivery-performance measurement layer**, not itself a release-risk score.

The initial DORA metrics for ReleaseGuard are:
1. Deployment Frequency
2. Lead Time for Changes
3. Change Failure Rate
4. Time to Restore Service

DORA data must come from observable delivery/deployment/incident events where possible.

### SOTA

In this project, **SOTA means State-of-the-Art release intelligence capabilities**, not a fifth standardized metric.

SOTA capabilities include:
- AI-assisted contextual release-risk analysis.
- Evidence aggregation across DevOps tools.
- Historical release/incident pattern detection.
- Change-risk analysis.
- Security context.
- Infrastructure-as-Code context.
- Deployment/runtime health.
- Explainable recommendations.
- Human-in-the-loop release governance.
- DORA-aware contextual risk.

Do not invent a formal external “SOTA score” unless a future requirement explicitly defines one.

## 3. Source of Truth

Before changing code:
1. Read `AGENTS.md`.
2. Read `docs/PROJECT.md`.
3. Read relevant sections of:
   - `docs/REQUIREMENTS.md`
   - `docs/ARCHITECTURE.md`
   - `docs/TECH_STACK.md`
   - `docs/DECISIONS.md`
   - `docs/CONTRACTS.md`
   - `docs/TASKS.md`
   - `docs/TESTING.md`
   - `docs/DEVELOPMENT.md`
4. Check `docs/CONTEXT.md` for current implementation status.

If code conflicts with these documents, do not silently choose a side. Report the conflict.

## 4. Product Rules

- ReleaseGuard is a governance/intelligence layer.
- Human approval remains part of the primary target workflow.
- DORA measures delivery performance; it should not be confused with release risk.
- AI must not be presented as a guaranteed predictor of production incidents.
- Deterministic rules and AI reasoning must remain conceptually separate.
- Risk decisions must be explainable and auditable.
- DORA metrics must be traceable to source events and calculation definitions.
- SOTA capabilities must be described as product capabilities, not unsupported marketing claims.
- Synthetic historical data must be clearly labeled.
- Missing source data must be represented as unknown/unavailable, not safe.
- Do not expand scope without approval.
- Do not replace working technologies without a documented reason.
- Do not add dependencies merely for convenience.
- Never hard-code secrets.
- Do not expose sensitive operational data unnecessarily in logs or AI prompts.

## 5. AI Agent Workflow

1. Understand the requested task.
2. Read the relevant project documents.
3. Check current implementation before coding.
4. Identify requirements and acceptance criteria.
5. Check architectural constraints and previous decisions.
6. Produce a concise implementation plan.
7. Implement the smallest correct change.
8. Run relevant tests/checks.
9. Review against requirements.
10. Update documentation if the current project state or a decision changed.
11. Report changes, verification, and unresolved uncertainty.

## 6. Anti-Drift Rules

Agents must not:
- Build every possible enterprise integration at once.
- Add Kubernetes merely to increase the technology count.
- Introduce a database before its use case is justified.
- Turn DORA into a risk score without an explicit approved model.
- Treat DORA metrics as proof that a specific release is safe or unsafe.
- Create an unsupported SOTA score.
- Treat synthetic data as real enterprise history.
- Let an LLM silently override deterministic safety evidence.
- Perform unrelated refactoring.
- Rewrite large areas of the repository for small requirements.
- Implement hypothetical future features before they are approved.

## 7. ReleaseGuard Decision Principles

The primary flow is:

`Release → Evidence → DORA context + Risk context → AI explanation → Recommendation → Human approval`

Recommendations:
- **ALLOW / LOW** (score 0–30)
- **REQUIRE HUMAN REVIEW / MEDIUM** (score 31–60)
- **BLOCK / APPROVAL REQUIRED / HIGH** (score 61–100)

Thresholds and signal weights are in `DECISIONS.md` and `CONTRACTS.md`. The score must remain inspectable and must not be changed by the LLM.

Recommendation is not enforcement. MVP does not automatically stop production.

## 8. DORA Guardrails

DORA calculations must:
- use explicit formulas/definitions,
- retain source event timestamps,
- distinguish unavailable data from zero,
- avoid misleading averages,
- define the time window,
- expose the underlying event count where useful,
- be tested with known examples.

Initial metrics:
- Deployment Frequency.
- Lead Time for Changes.
- Change Failure Rate.
- Time to Restore Service.

## 9. Definition of Done

A task is complete only when:
- Acceptance criteria pass.
- Relevant tests pass.
- No unrelated behavior changed.
- Security-sensitive values are protected.
- DORA calculations are verified where applicable.
- AI behavior is grounded where applicable.
- Documentation reflects meaningful project-state changes.
- Remaining `UNKNOWN — requires confirmation` items are reported.
